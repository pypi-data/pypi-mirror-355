# JustServer

JustServer is a FastAPI-based service designed to manage multiple `justniffer` network sniffing instances in a concurrent, secure, and efficient manner. It exposes a simple RESTful interface for starting, stopping, listing, and restarting sniffers across network interfaces.

## 🚀 Features

- 🔐 API key protection on all operational routes
- 🧵 ThreadPoolExecutor for parallel instance handling
- ⚙️ Dynamic justniffer process spawning with configurable filters and encodings
- 📦 Built-in lifecycle management using FastAPI's `lifespan`
- 💻 Easy process tracking and UUID-based control

## 📦 API Endpoints

All operational endpoints are secured via the `X-API-Key` header.

- `POST /start`: Launch a new justniffer process
- `POST /stop/{uuid}`: Stop a specific sniffer instance
- `POST /stop-all`: Stop all running instances
- `POST /restart`: Restart with new settings
- `GET /list`: List active sniffer processes
- `GET /health`: Health check (unauthenticated)

## 🛠️ Configuration

JustServer uses environment-based configuration via `justserver.daemon.settings`. Key settings:

- `JUSTSERVER_API_KEY`: API key for authentication
- `JUSTSERVER_MAX_INSTANCES`: Maximum concurrent sniffer processes
- `JUSTSERVER_JUSTNIFFER_CMD`: Base justniffer executable command

## 🧪 Example Usage

```bash
curl -X POST http://localhost:8000/start \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"interface": "eth0", "filter": "tcp port 80"}'
