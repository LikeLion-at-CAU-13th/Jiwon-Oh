from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from config.custom_exceptions import BaseCustomException  # ← 경로는 프로젝트에 맞게 수정

class ExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        error_info = self._get_error_info(exception)

        response_data = self._create_unified_response(error_info)

        return JsonResponse(
            response_data,
            status=error_info.get('status_code', 500),
        )

    def _get_error_info(self, exception):
        # ✅ 1. 커스텀 예외 (BaseCustomException)
        if isinstance(exception, BaseCustomException):
            return {
                'message': exception.detail,
                'status_code': exception.status_code,
                'code': exception.code
            }

        # ✅ 2. 404 예외
        if isinstance(exception, Http404):
            return {
                'message': 'Resource not found.',
                'status_code': 404,
                'code': 'NOT-FOUND'
            }

        # ✅ 3. 권한 예외
        if isinstance(exception, PermissionDenied):
            return {
                'message': 'Permission denied.',
                'status_code': 403,
                'code': 'PERMISSION-DENIED'
            }

        # ✅ 4. 예상치 못한 일반 예외
        return {
            'message': str(exception),
            'status_code': 500,
            'code': 'INTERNAL-SERVER-ERROR'
        }

    def _create_unified_response(self, error_info):
        return {
            'success': False,
            'error': {
                'code': error_info.get('code', 'UNKNOWN_ERROR'),
                'message': error_info.get('message', 'An error occurred.'),
                'status_code': error_info.get('status_code', 500),
            }
        }
