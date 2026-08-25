import importlib
import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers

app = FastAPI(title="Quinielas de Futbol")
register_exception_handlers(app)

# En produccion la SPA vive en otro origen que la API (nexutest vs nexutest-api),
# asi que sin esto el navegador bloquea toda llamada autenticada.
_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGIN", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["ops"])
def healthz() -> dict[str, str]:
    """Liveness para el healthCheck del task de ECS."""
    return {"status": "ok"}


_ROUTER_MODULES = [
    "app.api.auth",
    "app.api.users",
    "app.api.wallet",
    "app.api.admin.catalog",
    "app.api.matches",
    "app.api.bets",
    "app.api.leaderboard",
    "app.api.admin.results",
]

for module_name in _ROUTER_MODULES:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name or (
            exc.name is not None and module_name.startswith(exc.name)
        ):
            continue
        raise
    else:
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            app.include_router(router)
