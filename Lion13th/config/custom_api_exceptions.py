from rest_framework.exceptions import APIException
from rest_framework import status

class BaseCustomAPIException(APIException):
    status_code = 500
    default_detail = "An unexpected error occurred."
    default_code = "UNEXPECTED-ERROR"

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        
        if code is None:
            code = self.default_code
        
        super().__init__(detail=detail, code=code)

class ConflictException(BaseCustomAPIException):
    status_code = 409
    default_detail = "A conflict occurred."
    default_code = "CONFLICT"

class PostConflictException(ConflictException):
    default_detail = "A conflict occurred with the post."
    default_code = "POST-CONFLICT"


class ShortCommentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "댓글은 최소 15자 이상이어야 합니다."
    default_code = "comment_too_short"
