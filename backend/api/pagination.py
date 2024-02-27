from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Кастомная настройка пагианции."""

    page_size = 6
    page_size_query_param = 'limit'
