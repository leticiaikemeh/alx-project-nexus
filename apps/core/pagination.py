from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination


class SmallResultsSetPagination(PageNumberPagination):
    """
    Page-number pagination tuned for small pages.

    Defaults:
        page_size: 5
        page_size_query_param: 'page_size' (client may override up to max_page_size)
        max_page_size: 10

    Query Params:
        - page (int, optional): 1-based page index.
        - page_size (int, optional): items per page (<= 10).
    """
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 10


class MediumResultsSetPagination(PageNumberPagination):
    """
    Page-number pagination for medium responses.

    Defaults:
        page_size: 20
        page_size_query_param: 'page_size'
        max_page_size: 50

    Query Params:
        - page (int, optional)
        - page_size (int, optional, <= 50)
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


class LargeResultsSetPagination(PageNumberPagination):
    """
    Page-number pagination for larger listings.

    Defaults:
        page_size: 50
        page_size_query_param: 'page_size'
        max_page_size: 100

    Query Params:
        - page (int, optional)
        - page_size (int, optional, <= 100)
    """
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100


class StandardLimitOffsetPagination(LimitOffsetPagination):
    """
    Limit/offset pagination for data-table style UIs.

    Defaults:
        default_limit: 20
        max_limit: 100

    Query Params:
        - limit (int, optional): items per page (<= 100). Defaults to 20.
        - offset (int, optional): number of records to skip.
    """
    default_limit = 20
    max_limit = 100


class ReviewCursorPagination(CursorPagination):
    """
    Cursor pagination for review feeds (stable ordering with high offsets).

    Defaults:
        page_size: 5
        ordering: '-created_at' (descending by creation time)

    Query Params:
        - cursor (string, optional): opaque position token returned by previous page.
    """
    page_size = 5
    ordering = "-created_at"
