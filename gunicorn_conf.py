import multiprocessing

# Server socket
bind = "0.0.0.0:8000"  # Listen on all network interfaces, port 8000

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Optimal for CPU-bound apps
worker_class = "uvicorn.workers.UvicornWorker"  # Required for FastAPI (ASGI)
timeout = 120  # Kill workers after 120s if they hang
keepalive = 5  # Keep-alive connections for 5s

# Logging
accesslog = "-"  # Log to stdout (useful for Docker)
errorlog = "-"   # Log errors to stdout
loglevel = "info"

# Security
limit_request_line = 4094  # Prevent oversized requests

# Prevent Gunicorn from starting if the app fails to load
preload_app = True

# Handle SIGTERM gracefully (for Docker/Kubernetes)
graceful_timeout = 30
