# Khandhas Sample App

A sample application demonstrating how to use the khandhas package in both development and production modes.

## Features

- **Development Mode**: Live reloading, debug mode, local package usage
- **Production Mode**: Optimized performance, installed package usage
- **Environment-based Configuration**: Switch modes using environment variables
- **Custom Routes**: Extended API endpoints beyond the basic application
- **Health Checks**: Built-in health monitoring
- **API Documentation**: Automatic OpenAPI/Swagger documentation

## Quick Start

### Prerequisites

Before running the sample app, you need to set up a Python virtual environment:

```bash
# Create virtual environment (run this once)
python -m venv .venv

# Activate virtual environment (run this every time you work on the project)
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows
```

### Development Mode (Default)

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 2. Install the package in development mode
cd ../packages/python-lib
pip install -e .

# 3. Go back to sample app and run
cd ../../sample-app
python main.py
```

### Production Mode

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 2. Install the package normally
pip install khandhas

# 3. Set production mode and run
export KHANDHAS_DEV_MODE=false
python main.py
```

### Using Environment Files

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Development mode
python main.py --env-file .env

# Production mode
python main.py --env-file .env.prod
```

## API Endpoints

Once the server is running, you can access:

- `GET /` - Welcome message and endpoint overview
- `GET /health` - Health check endpoint
- `GET /api/v1/info` - Server information
- `POST /api/v1/echo` - Echo endpoint for testing
- `GET /api/v1/sample` - Sample custom endpoint
- `GET /api/v1/toggle-mode` - Mode switching information
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Configuration

### Environment Variables

The app can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KHANDHAS_DEV_MODE` | Enable development mode | `true` |
| `KHANDHAS_HOST` | Server host | `0.0.0.0` |
| `KHANDHAS_PORT` | Server port | `8000` |
| `KHANDHAS_DEBUG` | Debug mode | `true` in dev, `false` in prod |
| `KHANDHAS_RELOAD` | Auto-reload on changes | `true` in dev, `false` in prod |
| `KHANDHAS_LOG_LEVEL` | Logging level | `DEBUG` in dev, `INFO` in prod |
| `KHANDHAS_API_PREFIX` | API prefix | `/api/v1` |
| `KHANDHAS_CORS_ORIGINS` | CORS origins | `*` |
| `KHANDHAS_SECRET_KEY` | Secret key | `sample-app-secret-key` |

### Command Line Arguments

```bash
python main.py --help
```

Options:
- `--mode {dev,prod}` - Override mode
- `--host HOST` - Server host
- `--port PORT` - Server port
- `--no-reload` - Disable auto-reload

## Development vs Production

### Development Mode

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 2. Enable development mode
export KHANDHAS_DEV_MODE=true
python main.py
```

### Production Mode

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 2. Enable production mode
export KHANDHAS_DEV_MODE=false
python main.py
```

## Usage Examples

### Basic Usage

```python
from khandhas_server import KhandhasServer, ServerConfig

# Create server
server = KhandhasServer()

# Add custom routes
app = server.get_app()

@app.get("/custom")
async def custom_endpoint():
    return {"message": "Custom endpoint"}

# Run server
server.run()
```

### Advanced Configuration

```python
from khandhas_server import KhandhasServer, ServerConfig

# Custom configuration
config = ServerConfig(
    host="127.0.0.1",
    port=8080,
    debug=True,
    reload=True,
    log_level="DEBUG",
    cors_origins=["http://localhost:3000"],
    api_prefix="/api/v2",
)

# Create server with config
server = KhandhasServer(config)

# Add startup handler
async def startup():
    print("Server starting up...")

server.add_startup_handler(startup)

# Run server
server.run()
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Sample endpoint
curl http://localhost:8000/api/v1/sample

# Echo endpoint
curl -X POST http://localhost:8000/api/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World"}'

# Mode information
curl http://localhost:8000/api/v1/toggle-mode
```

## Hot Reloading in Development

When running in development mode, the server will automatically reload when you make changes to:

- Python files in the package
- Configuration files
- Environment variables

This makes development much faster as you don't need to manually restart the server.

## Switching Between Modes

**Note**: Always activate your virtual environment first:
```bash
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows
```

### Method 1: Environment Variable

```bash
# Development mode
export KHANDHAS_DEV_MODE=true
python main.py

# Production mode
export KHANDHAS_DEV_MODE=false
python main.py
```

### Method 2: Command Line

```bash
# Development mode
python main.py --mode dev

# Production mode
python main.py --mode prod
```

### Method 3: Environment File

```bash
# Development mode
cp .env.dev .env
python main.py

# Production mode
cp .env.prod .env
python main.py
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV KHANDHAS_DEV_MODE=false
ENV KHANDHAS_HOST=0.0.0.0
ENV KHANDHAS_PORT=8000

EXPOSE 8000

CMD ["python", "main.py"]
```

### Systemd Service

```ini
[Unit]
Description=Khandhas Server Sample App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/khandhas-sample-app
Environment=KHANDHAS_DEV_MODE=false
Environment=KHANDHAS_HOST=0.0.0.0
Environment=KHANDHAS_PORT=8000
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Virtual Environment Issues

Make sure you've activated your virtual environment:

```bash
# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Verify activation (should show virtual environment path)
which python  # Linux/Mac
where python  # Windows
```

### Import Errors

If you get import errors, make sure the package is installed in your virtual environment:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Development mode
cd ../packages/python-lib
pip install -e .

# Production mode
pip install khandhas
```

### Port Already in Use

If the port is already in use, change it:

```bash
# Make sure virtual environment is activated
source .venv/bin/activate
python main.py --port 8001
```

### Permission Denied

If you get permission denied errors:

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Use a different port
python main.py --port 8080

# Or run as root (not recommended)
sudo python main.py
```

### Dependencies Not Found

If you get module not found errors:

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or reinstall the package
pip install -e ../packages/python-lib
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in both development and production modes
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
