from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.engine.errors import (
    AlreadySettled,
    BettingClosed,
    DomainError,
    InsufficientCredits,
    InvalidSelection,
    NotFound,
    StakeOutOfRange,
)

_STATUS_BY_ERROR: dict[type[Exception], int] = {
    BettingClosed: status.HTTP_409_CONFLICT,
    InsufficientCredits: status.HTTP_402_PAYMENT_REQUIRED,
    StakeOutOfRange: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidSelection: status.HTTP_422_UNPROCESSABLE_CONTENT,
    AlreadySettled: status.HTTP_409_CONFLICT,
    NotFound: status.HTTP_404_NOT_FOUND,
}


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = _STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
