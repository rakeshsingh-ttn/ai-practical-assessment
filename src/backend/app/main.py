from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.app.config import settings
from src.backend.app.error_handlers import register_error_handlers
from src.backend.app.routers import auth, health, tickets, users


def create_app() -> FastAPI:
    app = FastAPI(title="Support Ticket Management System", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(tickets.router, prefix="/api")

    return app


app = create_app()
