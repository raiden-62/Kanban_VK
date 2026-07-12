from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import init_db
from app.routers import auth, boards, cards, columns, comments, labels, roles, users


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(boards.router, prefix=settings.api_prefix)
    app.include_router(roles.router, prefix=settings.api_prefix)
    app.include_router(labels.router, prefix=settings.api_prefix)
    app.include_router(columns.router, prefix=settings.api_prefix)
    app.include_router(cards.router, prefix=settings.api_prefix)
    app.include_router(comments.router, prefix=settings.api_prefix)

    return app


app = create_app()
