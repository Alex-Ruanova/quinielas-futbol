import importlib

from fastapi import APIRouter, FastAPI

from app.api.exception_handlers import register_exception_handlers

app = FastAPI(title="Quinielas de Futbol")
register_exception_handlers(app)

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
