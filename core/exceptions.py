from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# Custom exception types 

class EunoiaError(Exception):
    """Base for all app-specific exceptions."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(EunoiaError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found."


class ConflictError(EunoiaError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists."


class UnauthorizedError(EunoiaError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required."


class ForbiddenError(EunoiaError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have permission to perform this action."


class ValidationError(EunoiaError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed."


class MediaProcessingError(EunoiaError):
    """Raised when Whisper / DeepFace / Librosa processing fails."""
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Media analysis failed. Falling back to CBT template mode."


# Handler registration 

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EunoiaError)
    async def eunoia_error_handler(_: Request, exc: EunoiaError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        # Never leak internal stack traces to the client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )