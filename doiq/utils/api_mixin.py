from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework import permissions, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from url_filter.integrations.drf import DjangoFilterBackend


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'count'
    max_page_size = 100

    def get_paginated_response(self, data):
        self.page.has_next()
        return Response({
            'links': {
                'next': self.get_next_link() if self.page.has_next() else None,
                'previous': self.get_previous_link() if self.page.has_previous() else None
            },
            'next_page': self.page.next_page_number() if self.page.has_next() else None,
            'count': self.page.paginator.count,
            'results': data
        })


class DefaultsMixin(object):
    """Default settings for view authentication, permissions,
    filtering and pagination."""
    permission_classes = (
        # IsAjaxOnly,
        # permissions.IsAuthenticated,
        permissions.AllowAny,
    )
    authentication_classes = (JSONWebTokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    ordering_fields = '__all__'
