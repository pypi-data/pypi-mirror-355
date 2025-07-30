from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import MCPStoreException, ErrorCode
import logging
from typing import Union
from pydantic import ValidationError

logger = logging.getLogger(__name__)

async def mcp_exception_handler(request: Request, exc: MCPStoreException):
    logger.error(f"Error occurred: {exc.code} - {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def validation_exception_handler(request: Request, exc: Union[ValidationError, ValueError]):
    logger.error(f"Validation error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Validation error",
                "details": {
                    "errors": str(exc)
                }
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": "Internal server error",
                "details": {
                    "error": str(exc)
                }
            }
        }
    ) 
