from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10


class MediumResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class StandardLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class ReviewCursorPagination(CursorPagination):
    page_size = 5
    ordering = '-created_at'
