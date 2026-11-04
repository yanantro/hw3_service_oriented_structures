import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("booking")


class ApiError(Exception):
    def __init__(self, status: int, error_code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status = status
        self.error_code = error_code
        self.message = message
        self.details = details


def body(error_code: str, message: str, details: dict | None = None) -> dict:
    return {"error_code": error_code, "message": message, "details": details}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status, content=body(exc.error_code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"], "type": err["type"]}
            for err in exc.errors()
        ]
        return JSONResponse(status_code=400, content=body("VALIDATION_ERROR", "request validation failed", {"errors": errors}))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "INTERNAL_ERROR")
        return JSONResponse(status_code=exc.status_code, content=body(code, str(exc.detail).lower()))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        log.exception("unhandled error")
        return JSONResponse(status_code=500, content=body("INTERNAL_ERROR", "internal server error"))
