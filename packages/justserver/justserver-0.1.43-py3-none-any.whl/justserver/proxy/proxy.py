import asyncio
from typing import Any
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, Request, HTTPException
import httpx
from justserver.model import Justniffer, StartResponse
from pydantic import BaseModel
from uuid import uuid4
from justserver.logging import logger
from justserver.proxy.endpoints import endpoints_collector
WAIT_TIMEOUT = 20

HOP_BY_HOP_HEADERS: set[str] = {
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailers',
    'transfer-encoding',
    'upgrade',
    'proxy-connection',
    'content-length',
    'content-encoding',
    'host'  # Filter host header
}


class ErrorResponse(BaseModel):
    type: str
    message: str


def filter_hop_by_hop_headers(headers: Any) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(follow_redirects=False) as client:
        app.state.client = client
        logger.info('httpx.AsyncClient started.')
        yield
    logger.info('httpx.AsyncClient closed.')


app = FastAPI(lifespan=lifespan)

collector = endpoints_collector()


@app.get('/health')
async def health_check():
    return {'status': 'healthy'}


@app.post('/start')
async def start(request: Request) -> Any:
    jusniffer = Justniffer(**await request.json())
    jusniffer.uuid = str(uuid4())
    body_str = jusniffer.model_dump_json()
    return await reverse_proxy(request=request, path='start', body=body_str.encode('utf-8'))


@app.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH', 'TRACE'])
async def reverse_proxy(request: Request, path: str, body: bytes | None = None):
    client: httpx.AsyncClient = request.app.state.client
    tasks = []
    urls = collector.get_endoints()
    logger.info(f'proxying request: {request.method} {path} to {urls}')
    for url in urls:
        target_url = httpx.URL(f'{url}/{path}', params=request.query_params)
        try:
            tasks.append(call_upstream(request, client, target_url, body))
        except httpx.HTTPError as exc:
            logger.error(f'http error forwarding request: {exc}')
            continue
    results = await asyncio.gather(*tasks, return_exceptions=True)

    def _as_json(result: httpx.Response | BaseException) -> Any:
        if isinstance(result, httpx.Response):
            return result.json()
        return ErrorResponse(type=result.__class__.__name__, message=str(result))

    return [_as_json(result) for result in results]


async def call_upstream(request: Request, client: httpx.AsyncClient, target_url: httpx.URL, req_body: bytes | None = None) -> httpx.Response:
    logger.info(f'proxying request: {request.method} {target_url}')
    req_headers = filter_hop_by_hop_headers(request.headers)
    X_FORWARDED_FOR = 'x-forwarded-for'
    assert request.client is not None
    if X_FORWARDED_FOR in req_headers:
        req_headers[X_FORWARDED_FOR] += f', {request.client.host}'
    else:
        req_headers[X_FORWARDED_FOR] = request.client.host
    if req_body is  None:
        req_body = await request.body()
    try:
        backend_req = client.build_request(
            method=request.method,
            url=target_url,
            headers=req_headers,
            content=req_body,
            cookies=request.cookies,
            timeout=httpx.Timeout(WAIT_TIMEOUT),
        )
        backend_resp = await client.send(backend_req)
        return backend_resp
    except httpx.TimeoutException as exc:
        logger.error(f'timeout error forwarding request:  {target_url} {exc}')
        raise HTTPException(status_code=504, detail=f'gateway timeout: {str(exc)}')
    except httpx.RequestError as exc:
        logger.error(f'error forwarding request: {exc}')
        raise HTTPException(status_code=503, detail=f'{target_url} service unavailable: {str(exc)}')
