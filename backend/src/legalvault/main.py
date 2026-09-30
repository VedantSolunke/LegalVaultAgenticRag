import uvicorn
from fastapi import FastAPI

from legalvault.api.health import router as health_router
from legalvault.api.research import router as research_router
from legalvault.api.sessions import router as sessions_router
from legalvault.api.traces import router as traces_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="LegalVault Research API",
        description="BNS legal research assistant backend",
        version="0.1.0",
    )
    app.include_router(health_router)
    app.include_router(research_router)
    app.include_router(sessions_router)
    app.include_router(traces_router)
    return app


def run() -> None:
    uvicorn.run(
        "legalvault.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
