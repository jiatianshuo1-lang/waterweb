from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '业务处理失败'
    default_code = 'business_error'

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        if detail is None:
            detail = self.default_detail
        if code is not None:
            self.default_code = code
        self.detail = detail
        self.code = code or self.default_code


class NotFoundException(BusinessException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '资源不存在'
    default_code = 'not_found'


class PermissionDeniedException(BusinessException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '没有操作权限'
    default_code = 'permission_denied'


class ValidationException(BusinessException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = '数据校验失败'
    default_code = 'validation_error'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'code': getattr(exc, 'code', response.status_code),
            'message': response.data if isinstance(response.data, str) else _extract_error_message(response.data),
            'data': None,
        }
        return response

    if isinstance(exc, Exception):
        from django.http import Http404
        from django.db import IntegrityError

        if isinstance(exc, Http404):
            return Response(
                {'code': 404, 'message': '资源不存在', 'data': None},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, IntegrityError):
            return Response(
                {'code': 400, 'message': '数据完整性错误', 'data': None},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('Unhandled exception: %s', str(exc))
            return Response(
                {'code': 500, 'message': '服务器内部错误', 'data': None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return response


def _extract_error_message(data):
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        errors = []
        for field, messages in data.items():
            if isinstance(messages, list):
                errors.append(f'{field}: {"; ".join(str(m) for m in messages)}')
            else:
                errors.append(f'{field}: {messages}')
        return '; '.join(errors)
    return str(data)


from rest_framework.response import Response
