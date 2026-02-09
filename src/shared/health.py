"""Health server utilities for microservices."""
import asyncio
from typing import Callable, Optional

import uvicorn
from fastapi import FastAPI


def create_health_app(
    service_name: str,
    health_check: Optional[Callable[[], bool]] = None
) -> FastAPI:
    app = FastAPI(title=f"{service_name} Health")

    @app.get("/health")
    async def health():
        if health_check is not None:
            is_healthy = health_check()
            if not is_healthy:
                return {"status": "unhealthy"}, 503
        return {"status": "healthy"}

    return app


async def run_health_server(
    service_name: str,
    port: int,
    health_check: Optional[Callable[[], bool]] = None
) -> None:
    """Run health server asynchronously."""
    app = create_health_app(service_name, health_check)

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="warning"
    )
    server = uvicorn.Server(config)
    await server.serve()


def start_health_server_background(
    service_name: str,
    port: int,
    health_check: Optional[Callable[[], bool]] = None
) -> asyncio.Task:
    """Start health server in background."""
    return asyncio.create_task(
        run_health_server(service_name, port, health_check)
    )
