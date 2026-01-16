from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN


class BadRequestException(HTTPException):
    def __init__(self, detail="Bad request"):
        super().__init__(status_code=HTTP_400_BAD_REQUEST, detail=detail)

class ValueControlException(BadRequestException):
    def __init__(self, detail="Valeur incorrecte"):
        super().__init__(detail=detail)

class NotFoundException(HTTPException):
    def __init__(self, detail="Resource not found"):
        super().__init__(status_code=HTTP_404_NOT_FOUND, detail=detail)

class ForbiddenException(HTTPException):
    def __init__(self, detail="You are not allowed to perform this action"):
        super().__init__(status_code=HTTP_403_FORBIDDEN, detail=detail)

class RenderError(Exception):
    def __init__(self, message: str, *, step: str | None = None, code: str | None = None, stack: str | None = None):
        self.step = step
        self.code = code
        self.stack = stack
        super().__init__(message)

    def as_dict(self):
        return {
            "message": str(self),
            "step": self.step,
            "code": self.code,
            "stack": self.stack,
        }
