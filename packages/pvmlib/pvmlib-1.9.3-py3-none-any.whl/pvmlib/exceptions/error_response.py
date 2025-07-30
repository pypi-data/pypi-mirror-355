from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pvmlib.responses.error_response import ErrorResponseException
from pvmlib.utils import Utils
from pvmlib.logs import LoggerSingleton, LogType
import json
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND
)

EVENT_TYPES = {
    HTTP_500_INTERNAL_SERVER_ERROR: "SERVER_ERROR",
    HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
    HTTP_404_NOT_FOUND: "NOT_FOUND",
    HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    ErrorResponseException: "ERROR_RESPONSE"
}

class ExceptionHandlers:
    """
    A class that defines custom exception handlers for FastAPI.

    This class centralizes the handling of various HTTP exceptions, providing consistent
    error logging and response formatting.  It uses the ErrorResponseException class
    to generate standardized error responses.
    """
    def __init__(self):
        """
        Initializes the ExceptionHandlers class.
        """
        self.log = LoggerSingleton().logger

    async def internal_server_error_exception_handler(self, request: Request, exc: Exception):
        """
        Handles internal server errors (HTTP 500).

        Logs the error and returns a JSON response with a 500 status code.

        Args:
            request (Request): The incoming Starlette request.
            exc (Exception): The raised exception.

        Returns:
            JSONResponse: A JSON response representing the error.
        """
        error_message, error_info = await Utils.get_instance_exception(exc)
        response = ErrorResponseException(
            message=error_message,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )
        additional_info = {
            "url": str(request.url),
            "method": request.method,
            "path": request.url.path,
            "endpoint": request.scope.get("endpoint").__name__ if request.scope.get("endpoint") else None
        }
        self.log.error(
            message=error_info,
            log_type=LogType.INTERNAL,
            event_type=EVENT_TYPES[HTTP_500_INTERNAL_SERVER_ERROR],
            status=str(HTTP_500_INTERNAL_SERVER_ERROR),
            additional_info=additional_info
        )
        return JSONResponse(content=json.loads(response.detail), status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    async def validation_exception_handler(self, request: Request, exc: RequestValidationError):
        """
        Handles request validation errors (HTTP 422).

        Formats the validation error details and returns a JSON response with a 422 status code.

        Args:
            request (Request): The incoming Starlette request.
            exc (RequestValidationError): The raised RequestValidationError exception.

        Returns:
            JSONResponse: A JSON response representing the validation error.
        """
        error_details = Utils.get_error_details(exc.errors())
        error_message = "Validation error: " + ", ".join(error_details)
        response = ErrorResponseException(
            message=error_message,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY
        )
        return JSONResponse(content=json.loads(response.detail), status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    async def not_found_exception_handler(self, request: Request, exc: HTTPException):
        """
        Handles "Not Found" errors (HTTP 404).

        Returns a JSON response with a 404 status code.

        Args:
            request (Request): The incoming Starlette request.
            exc (HTTPException): The raised HTTPException.

        Returns:
            JSONResponse: A JSON response representing the "Not Found" error.
        """
        error_message = "Resource not found"
        response = ErrorResponseException(
            message=error_message,
            status_code=HTTP_404_NOT_FOUND
        )
        return JSONResponse(content=json.loads(response.detail), status_code=exc.status_code)

    async def method_not_allowed_exception_handler(self, request: Request, exc: HTTPException):
        """
        Handles "Method Not Allowed" errors (HTTP 405).

        Returns a JSON response with a 405 status code.

        Args:
            request (Request): The incoming Starlette request.
            exc (HTTPException): The raised HTTPException.

        Returns:
            JSONResponse: A JSON response representing the "Method Not Allowed" error.
        """
        error_message = "Method not allowed."
        response = ErrorResponseException(
            message=error_message,
            status_code=HTTP_405_METHOD_NOT_ALLOWED
        )
        return JSONResponse(content=json.loads(response.detail), status_code=exc.status_code)

    async def bad_request_exception_handler(self, request: Request, exc: HTTPException):
        """
        Handles "Bad Request" errors (HTTP 400).

        Returns a JSON response with a 400 status code.

        Args:
            request (Request): The incoming Starlette request.
            exc (HTTPException): The raised HTTPException.

        Returns:
            JSONResponse: A JSON response representing the "Bad Request" error.
        """
        error_message = "Bad request."
        response = ErrorResponseException(
            message=error_message,
            status_code=HTTP_400_BAD_REQUEST
        )
        return JSONResponse(content=json.loads(response.detail), status_code=exc.status_code)

    async def error_exception_handler(self, request: Request, exc: ErrorResponseException):
        """
        Handles custom ErrorResponseException.

        Returns a JSON response with the error details from the ErrorResponseException.

        Args:
            request (Request): The incoming Starlette request.  (Not used, but included for consistency).
            exc (ErrorResponseException): The raised ErrorResponseException.

        Returns:
            JSONResponse: A JSON response representing the custom error.
        """
        return JSONResponse(content=json.loads(exc.detail), status_code=exc.status_code)

def register_exception_handlers(app: FastAPI):
    """
    Registers custom exception handlers with the FastAPI application.

    This function adds the handlers defined in the ExceptionHandlers class to the
    FastAPI application instance.  These handlers will be invoked when the corresponding
    exceptions are raised during request processing.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    handlers = ExceptionHandlers()
    app.add_exception_handler(HTTP_500_INTERNAL_SERVER_ERROR, handlers.internal_server_error_exception_handler)
    app.add_exception_handler(RequestValidationError, handlers.validation_exception_handler)
    app.add_exception_handler(HTTP_404_NOT_FOUND, handlers.not_found_exception_handler)
    app.add_exception_handler(HTTP_405_METHOD_NOT_ALLOWED, handlers.method_not_allowed_exception_handler)
    app.add_exception_handler(HTTP_400_BAD_REQUEST, handlers.bad_request_exception_handler)
    app.add_exception_handler(ErrorResponseException, handlers.error_exception_handler)