from rest_framework.response import Response


def success_response(data=None, message='success', code=0, status_code=200):
    return Response({
        'code': code,
        'message': message,
        'data': data,
    }, status=status_code)


def created_response(data=None, message='创建成功'):
    return success_response(data=data, message=message, status_code=201)


def updated_response(data=None, message='更新成功'):
    return success_response(data=data, message=message, status_code=200)


def deleted_response(message='删除成功'):
    return success_response(message=message, status_code=204)
