"""Main FastAPI application with lifespan management."""

import logging
import warnings
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from .core.config import settings
from .core.database import close_db
from .routes import health, match, search, stats
from polus.aithena.clinical_aithena.rabbit import RabbitMQPublisher

# Configure application logging so pipeline progress is visible.
# Uvicorn only configures its own loggers; without this, our modules
# inherit the root logger's default WARNING level and all info/debug
# messages are silently suppressed.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Silence noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("aio_pika").setLevel(logging.WARNING)

# Suppress Pydantic serialization warnings for CTGovStudy JSONB columns.
# The JSONB data from PostgreSQL is stored as raw dicts, which triggers
# PydanticSerializationUnexpectedValue when the model has typed fields.
# The data still serializes correctly; these are cosmetic warnings.
warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings",
    category=UserWarning,
    module="pydantic",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.

    Handles startup and shutdown events:
    - Startup: Initialize RabbitMQ publisher
    - Shutdown: Close database and RabbitMQ connections
    """

    # Startup: connect RabbitMQ publisher (non-fatal if unavailable)
    publisher = RabbitMQPublisher()
    await publisher.connect(settings.rabbitmq_url)
    app.state.rabbitmq_publisher = publisher

    yield

    # Shutdown
    await publisher.disconnect()
    await close_db()
    logger.info("Database and RabbitMQ connections closed")


# Create FastAPI application
# root_path is set via API_ROOT_PATH env var (defaults to "").
# In Kubernetes, set API_ROOT_PATH="/apis/ctaithena" so OpenAPI docs
# generate correct URLs behind the reverse proxy.  Locally it stays
# empty so StaticFiles mounts work without a proxy.
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    root_path=settings.api_root_path,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(search.router)
app.include_router(stats.router)
app.include_router(match.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "documentation": "/documentation/",
        "health": "/health",
        "search": "/search",
        "stats": "/stats",
        "match": "/match",
    }


# ---------------------------------------------------------------------------
# Documentation site (mkdocs-material) — served via ASGI middleware
# ---------------------------------------------------------------------------
# We cannot use `app.mount("/documentation", StaticFiles(...))` because
# FastAPI's `root_path` setting (needed for OpenAPI docs behind the Nginx
# reverse proxy in Kubernetes) causes mounted sub-apps to expect the full
# prefixed path (e.g. /apis/ctaithena/documentation/...), but Nginx has
# already stripped the prefix.  The app therefore receives /documentation/
# which does not match.
#
# The fix: an ASGI middleware that intercepts /documentation requests
# **before** the FastAPI router, delegates to a standalone StaticFiles
# instance (with root_path=""), and falls through to FastAPI for everything
# else.  This works identically in local dev (root_path="") and in K8s
# (root_path="/apis/ctaithena").
# ---------------------------------------------------------------------------


class _DocsMiddleware:
    """ASGI middleware that serves docs from StaticFiles, bypassing root_path."""

    def __init__(self, fastapi_app: ASGIApp, docs_app: ASGIApp) -> None:
        self.fastapi_app = fastapi_app
        self.docs_app = docs_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].startswith("/documentation"):
            path: str = scope["path"]

            # Redirect /documentation -> /documentation/ so the browser
            # resolves relative links (CSS, JS, images) correctly.
            if path == "/documentation":
                redirect = RedirectResponse(
                    url=scope.get("root_path", "") + "/documentation/",
                    status_code=307,
                )
                await redirect(scope, receive, send)
                return

            # Strip the /documentation prefix and hand to StaticFiles
            remaining = path[len("/documentation"):] or "/"
            child_scope = dict(scope)
            child_scope["path"] = remaining
            child_scope["root_path"] = ""  # neutralise FastAPI's root_path
            await self.docs_app(child_scope, receive, send)
        else:
            await self.fastapi_app(scope, receive, send)


_docs_candidates = [
    Path("/app/site"),  # Docker: copied from docs-builder stage
    Path(__file__).resolve().parents[5] / "site",  # Local dev
]
_docs_site = next((p for p in _docs_candidates if p.is_dir()), None)
if _docs_site is not None:
    _static_docs = StaticFiles(directory=str(_docs_site), html=True)
    app = _DocsMiddleware(app, _static_docs)  # type: ignore[assignment]
    logger.info("Documentation site mounted at /documentation from %s", _docs_site)
else:
    logger.info(
        "Documentation site not found — /documentation will not be available. "
        "Run 'mkdocs build' to generate it, or build the Docker image."
    )
