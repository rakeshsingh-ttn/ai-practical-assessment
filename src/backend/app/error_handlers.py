from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.backend.app.exceptions import AppError


def _error_response(status_code: int, code: str, message: str, details: dict | list | None = None):
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        status_code = 409 if exc.code in {
            "invalid_transition",
            "ticket_not_editable",
            "comment_not_allowed",
        } else 404 if exc.code == "not_found" else 400
        return _error_response(status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        return _error_response(
            422,
            "validation_error",
            "Request validation failed",
            jsonable_encoder(exc.errors()),
        )
