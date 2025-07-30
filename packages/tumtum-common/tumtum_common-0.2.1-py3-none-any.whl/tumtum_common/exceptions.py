"""Exceptions for tumtum."""

class CodeException(Exception):
    def __init__(self, message: str, status_code: int):
        """Base class for exceptions that include an HTTP status code.
        Args:
            message (str): The error message.
            status_code (int): The HTTP status code associated with the error.
        """
        self.__message = message
        self.__status_code = status_code
        super().__init__(message)

    @property
    def message(self):
        """Return the error message."""
        return self.__message

    @property
    def status_code(self):
        """Return the HTTP status code associated with the error."""
        return self.__status_code


# 2xx
class OKException(CodeException):  # 200
    def __init__(self, message: str = "Resource successfully processed"):
        """Exception for HTTP 200 OK status code."""
        super().__init__(message=message, status_code=200)

class AcceptedException(CodeException):  # 202
    def __init__(self, message: str = "Resource accepted for processing"):
        """Exception for HTTP 202 Accepted status code."""
        super().__init__(message=message, status_code=202)

class NoContentException(CodeException):  # 204
    def __init__(self, message: str = "Resource successfully processed, no content to return"):
        """Exception for HTTP 204 No Content status code."""
        super().__init__(message=message, status_code=204)


# 4xx
class BadRequestException(CodeException):
    def __init__(self, message: str = "Invalid request"):
        """Exception for HTTP 400 Bad Request status code."""
        super().__init__(message=message, status_code=400)

class UnauthorizedException(CodeException):
    def __init__(self, message: str = "Unauthorized access"):
        """Exception for HTTP 401 Unauthorized status code."""
        super().__init__(message=message, status_code=401)

class PaymentRequiredException(CodeException):
    def __init__(self, message: str = "Payment required to access this resource."):
        """Exception for HTTP 402 Payment Required status code."""
        super().__init__(message=message, status_code=402)

class ForbiddenException(CodeException):
    def __init__(self, message: str = "Access to this resource is forbidden."):
        """Exception for HTTP 403 Forbidden status code."""
        super().__init__(message=message, status_code=403)

class NotFoundException(CodeException):
    def __init__(self, message: str = "Resource not found."):
        """Exception for HTTP 404 Not Found status code."""
        super().__init__(message=message, status_code=404)

class ConflictException(CodeException):
    def __init__(self, message: str = "Conflict with the current state of the resource."):
        """Exception for HTTP 409 Conflict status code."""
        super().__init__(message=message, status_code=409)


# 5xx
class InternalServerErrorException(CodeException):
    def __init__(self, message: str = "Internal server error occurred"):
        """Exception for HTTP 500 Internal Server Error status code."""
        super().__init__(message=message, status_code=500)

class NotImplementedException(CodeException):
    def __init__(self, message: str = "Feature not implemented"):
        """Exception for HTTP 501 Not Implemented status code."""
        super().__init__(message=message, status_code=501)

class BadGatewayException(CodeException):
    def __init__(self, message: str = "Bad gateway error occurred"):
        """Exception for HTTP 502 Bad Gateway status code."""
        super().__init__(message=message, status_code=502)


