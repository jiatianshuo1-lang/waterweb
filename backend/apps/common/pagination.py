from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'results': data,
            }
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'code': {'type': 'integer', 'example': 0},
                'message': {'type': 'string', 'example': 'success'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 123},
                        'next': {'type': 'string', 'nullable': True},
                        'previous': {'type': 'string', 'nullable': True},
                        'page': {'type': 'integer', 'example': 1},
                        'page_size': {'type': 'integer', 'example': 20},
                        'results': schema,
                    }
                }
            }
        }


class SmallPagination(StandardPagination):
    page_size = 10
    max_page_size = 50


class LargePagination(StandardPagination):
    page_size = 50
    max_page_size = 200
