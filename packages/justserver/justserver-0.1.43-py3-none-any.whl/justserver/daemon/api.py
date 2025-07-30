from fastapi import HTTPException
import os
import signal
from subprocess import Popen, PIPE, TimeoutExpired
from uuid import uuid4

from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import asynccontextmanager
from shlex import split
from fastapi import Body, Depends, FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from justserver.model import (Encoder, Justniffer, StartResponse, StopResponse, StopAllResponse, ListResponse,
                              FuturesDict, JustnifferProcess)
from justserver.daemon.settings import MAX_INSTANCES_ATTR, settings, get_setting_env_name
from justserver.logging import logger


WAIT_TIMEOUT = 2
FUTURE_TIMEOUT = WAIT_TIMEOUT + 1
MAX_WORKERS = 10
API_KEY_HEADER_NAME = "X-API-Key"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures: FuturesDict = {}
    app.state.futures = futures
    yield
    app.state.executor.shutdown(wait=False)
    for uuid in list(futures.keys()):
        _stop(uuid)


def _check_api_key(api_key: str = Depends(APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False))):
    if settings.api_key and api_key != settings.api_key:
        logger.error(f'{api_key} invalid API')
        raise HTTPException(status_code=401, detail='invalid API key')


app = FastAPI(lifespan=lifespan)

protected = APIRouter(
    dependencies=[
        Depends(_check_api_key)
    ]
)


def kill_and_wait(pid, sig=signal.SIGTERM, timeout=10):
    logger.info(f'killing {pid} with {sig}')
    os.kill(pid, sig)
    os.waitpid(pid, timeout)


def _get_justniffer_cmd() -> list[str]:
    return split(settings.justniffer_cmd)


def run_justniffer(justniffer: Justniffer) -> tuple[Popen | None, str | None]:
    justniffer_cmd = _get_justniffer_cmd()
    command = justniffer_cmd + ['-i', justniffer.interface]
    process = None
    if justniffer.encode:
        encode_flag = f'--{justniffer.encode.value.replace("_", "-")}'
        command.append(encode_flag)
    if justniffer.log_format:
        command.extend(['-l', f'{justniffer.log_format}'])
    if justniffer.filter:
        command.extend(['-p', f'{justniffer.filter}'])
    if justniffer.in_the_middle:
        command.append('-m')
    if justniffer.max_tcp_streams:
        command.extend(['-s', f'{justniffer.max_tcp_streams}'])
    if justniffer.truncated:
        command.append('-t')
    if not justniffer.newline:
        command.append('-N')
    logger.info(' '.join(command))
    try:
        process = Popen(command, stderr=PIPE)
    except Exception as e:
        msg = f'failed to start justniffer: {e}'
        logger.error(msg)
        return None, msg
    return_code = None
    try:
        process.wait(timeout=WAIT_TIMEOUT)
        return_code = process.returncode
        if (return_code) is not None and return_code != -9:
            stderr = process.stderr.read().decode() if process.stderr else ''
            process.wait()
            err_msg = f'command failed ({return_code}): {stderr.strip()}'
            logger.error(err_msg)
            return None, err_msg
            # return {'message': err_msg}
        else:
            logger.info(return_code)
            return process, None
    except TimeoutExpired as e:
        return process, None


@app.exception_handler(Exception)
def exception_handler(request, exc):
    return JSONResponse(content={'message': str(exc)}, status_code=500)


def _already_running(justniffer: Justniffer) -> JustnifferProcess | None:
    for uuid, process in app.state.futures.items():
        if process.justniffer_spec.__compare__(justniffer):
            return process
    return None


j_example = Justniffer(interface='eth0',
                       filter='tcp port 80 or tcp port 443',
                       encode=Encoder.unprintable,
                       max_tcp_streams=16384,
                       in_the_middle=False
                       )


@protected.post('/start')
def start(justniffer: Justniffer = Body(..., example=j_example)) -> StartResponse:
    uuid = justniffer.uuid or str(uuid4())
    try:
        jprocess = _already_running(justniffer)
        if jprocess:
            uuid = jprocess.uuid
            return StartResponse(uuid=uuid, message=f'justniffer {uuid} already running')
        else:
            futures = app.state.futures
            if len(futures) >= settings.max_instances:
                raise Exception(f'all {get_setting_env_name(settings, MAX_INSTANCES_ATTR)}={settings.max_instances} instances running')

            future: Future = app.state.executor.submit(run_justniffer, justniffer)
            process: Popen | None
            process, error_message = future.result(timeout=FUTURE_TIMEOUT)
            if error_message:
                raise Exception(error_message)
            if process:
                process.pid
                app.state.futures[uuid] = JustnifferProcess(pid=process.pid, uuid=uuid, justniffer_spec=justniffer)
    except TimeoutError as e:
        pass
    assert uuid, 'UUID should not be None'
    proccesses = len(app.state.futures)
    return StartResponse(uuid=uuid, message=f'justniffer {uuid} started of {proccesses}')


def _stop(uuid: str):
    futures: FuturesDict = app.state.futures
    process = futures[uuid]
    kill_and_wait(process.pid)
    app.state.futures.pop(uuid)


@protected.post('/restart')
def restart(justniffer: Justniffer = Body(..., example=j_example)) -> StartResponse:
    stop_all()
    return start(justniffer)


@protected.post('/stop/{uuid}')
def stop(uuid: str) -> StopResponse:
    if uuid in app.state.futures:
        _stop(uuid)
        return StopResponse(message=f'justniffer {uuid} stopped')
    else:
        return StopResponse(message=f'justniffer {uuid} not found')


@protected.post('/stop-all')
def stop_all() -> StopAllResponse:
    idx = -1
    for idx, uuid in enumerate(app.state.futures.copy().keys()):
        _stop(uuid)
        logger.info(f'justniffer {uuid} stopped')
    return StopAllResponse(message=f'all {idx+1} justniffers stopped')


@protected.get('/list')
def get_list() -> ListResponse:
    return ListResponse(processes=app.state.futures, message=f'{len(app.state.futures)} justniffers running')


@app.get('/health', response_class=JSONResponse)
async def health_check():
    return {"status": "healthy"}


app.include_router(protected)
