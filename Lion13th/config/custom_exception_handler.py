from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError, ErrorDetail
from rest_framework.response import Response
from config.custom_exceptions import BaseCustomException  # ← 경로는 프로젝트 구조에 따라 조정

def custom_exception_handler(exc, context):
    # 기본 DRF 핸들러로 처리 가능한 예외는 먼저 처리
    response = drf_exception_handler(exc, context)

    # ✅ 1. ValidationError 처리
    if isinstance(exc, ValidationError):
        error_detail = {
            "success": False,
            "error": {
                "code": "validation_error",
                "message": f"{len(exc.detail)} validation errors occurred",
                "fields": exc.detail,
                "status_code": 400,
            }
        }
        return Response(error_detail, status=400)

    # ✅ 2. BaseCustomException 처리
    if isinstance(exc, BaseCustomException):
        return Response({
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }, status=exc.status_code)

    # ✅ 3. DRF가 처리한 응답 포맷 정리
    if response is not None and response.data:
        unified_data = _create_unified_response(response)
        return Response(unified_data, status=response.status_code)

    # ✅ 4. 완전히 처리 불가능한 에러
    return Response({
        "success": False,
        "error": {
            "code": "unknown_error",
            "message": "Unexpected server error occurred.",
            "status_code": 500
        }
    }, status=500)


def _create_unified_response(response):
    """
    DRF 기본 예외 응답을 프론트엔드가 요구하는 포맷으로 변환
    """
    try:
        error_detail = _extract_error_detail(response.data)
    except Exception as e:
        error_detail = {
            'code': 'internal_error',
            'message': f'Exception in custom handler: {str(e)}'
        }

    return {
        'success': False,
        'error': {
            'code': error_detail.get('code', 'DRF-API-ERROR'),
            'message': error_detail.get('message', 'An error occurred.'),
            'status_code': response.status_code,
            'fields': error_detail.get('fields', None)
        }
    }


def _extract_error_detail(error_data):
    """
    다양한 DRF 응답 형태에서 주요 메시지, 코드, 필드 에러를 추출
    """
    if isinstance(error_data, str):
        return {
            'message': error_data,
            'code': 'api_error'
        }

    if isinstance(error_data, list) and error_data:
        first_error = error_data[0]
        if isinstance(first_error, str):
            return {
                'message': first_error,
                'code': 'validation_error'
            }
        elif isinstance(first_error, dict):
            return _extract_error_detail(first_error)

    if isinstance(error_data, ErrorDetail):
        return {
            'message': str(error_data),
            'code': getattr(error_data, 'code', 'unknown_error')
        }

    if isinstance(error_data, dict):
        if 'message' in error_data and 'code' in error_data:
            return error_data

        if 'detail' in error_data:
            return {
                'message': str(error_data['detail']),
                'code': getattr(error_data['detail'], 'code', 'unknown_error')
            }

        field_errors = []
        for field, messages in error_data.items():
            if isinstance(messages, list) and messages:
                field_errors.append(f"{field}: {messages[0]}")
            else:
                field_errors.append(f"{field}: {str(messages)}")

        if field_errors:
            return {
                'message': f"{len(field_errors)} validation errors occurred",
                'code': 'validation_error',
                'fields': error_data
            }

    return {
        'message': str(error_data),
        'code': 'unknown_error'
    }
