from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_error_handlers(app: FastAPI):

    # Bắt tất cả HTTPException (bao gồm cả các custom exception ở trên)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )

    # Bắt lỗi validation của Pydantic (VD: thiếu field, sai kiểu dữ liệu)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "success": False,
                "error": {
                    "code": 422,
                    "message": "Dữ liệu gửi lên không hợp lệ",
                    "details": exc.errors(),
                }
            },
        )

    # Bắt các lỗi không lường trước (500) — tránh lộ traceback cho client
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": 500,
                    "message": "Đã có lỗi xảy ra ở server, vui lòng thử lại sau",
                }
            },
        )