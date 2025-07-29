"""
See: https://www.django-rest-framework.org/api-guide/pagination/
"""

from rest_framework.pagination import PageNumberPagination as DRFPageNumberPagination
from rest_framework.response import Response


class PageNumberPagination(DRFPageNumberPagination):
    # Required to enable client to control page size
    page_size_query_param = 'page_size'
    max_page_size = 500

    def get_paginated_response(self, data, meta=None):
        metadata = dict(meta) if meta else {}

        metadata['pagination'] = {
            'current_page': self.page.number,
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'per_page': self.page.paginator.per_page,
            'total': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
        }

        return Response({
            'data': data,
            'meta': metadata,
        })
