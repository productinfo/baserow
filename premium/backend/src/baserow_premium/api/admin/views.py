from typing import Dict, List
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions
from baserow.api.errors import (
    ERROR_INVALID_SORT_ATTRIBUTE,
    ERROR_INVALID_SORT_DIRECTION,
    ERROR_INVALID_FILTER_ATTRIBUTE,
)
from baserow.api.exceptions import (
    InvalidFilterAttributeException,
    InvalidSortAttributeException,
    InvalidSortDirectionException,
)
from baserow.api.mixins import (
    SearchableViewMixin,
    SortableViewMixin,
    FilterableViewMixin,
)
from baserow.api.pagination import PageNumberPagination
from baserow.api.schemas import get_error_schema


class AdminListingView(
    APIView, SearchableViewMixin, SortableViewMixin, FilterableViewMixin
):
    permission_classes = (IsAdminUser,)
    serializer_class = None
    search_fields: List[str] = ["id"]
    filters_field_mapping: Dict[str, str] = {}
    sort_field_mapping: Dict[str, str] = {}

    @map_exceptions(
        {
            InvalidSortDirectionException: ERROR_INVALID_SORT_DIRECTION,
            InvalidSortAttributeException: ERROR_INVALID_SORT_ATTRIBUTE,
            InvalidFilterAttributeException: ERROR_INVALID_FILTER_ATTRIBUTE,
        }
    )
    def get(self, request):
        """
        Responds with paginated results related to queryset and the serializer
        defined on this class.
        """

        search = request.GET.get("search")
        sorts = request.GET.get("sorts")
        filters = self.parse_filters(request.GET.get("filters"))

        queryset = self.get_queryset(request)
        queryset = self.apply_filters(filters, queryset)
        queryset = self.apply_search(search, queryset)
        queryset = self.apply_sorts_or_default_sort(sorts, queryset)

        paginator = PageNumberPagination(limit_page_size=100)
        page = paginator.paginate_queryset(queryset, request, self)
        serializer = self.get_serializer(request, page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def get_queryset(self, request):
        raise NotImplementedError("The get_queryset method must be set.")

    def get_serializer(self, request, *args, **kwargs):
        if not self.serializer_class:
            raise NotImplementedError(
                "Either the serializer_class must be set or the get_serializer method "
                "must be overwritten."
            )

        return self.serializer_class(*args, **kwargs)

    @staticmethod
    def get_extend_schema_parameters(
        name, serializer_class, search_fields, sort_field_mapping
    ):
        """
        Returns the schema properties that can be used in in the @extend_schema
        decorator.
        """

        fields = sort_field_mapping.keys()
        all_fields = ", ".join(fields)
        field_name_1 = "field_1"
        field_name_2 = "field_2"
        for i, field in enumerate(fields):
            if i == 0:
                field_name_1 = field
            if i == 1:
                field_name_2 = field

        return {
            "parameters": [
                OpenApiParameter(
                    name="search",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.STR,
                    description=f"If provided only {name} that match the query will "
                    f"be returned.",
                ),
                OpenApiParameter(
                    name="sorts",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.STR,
                    description=f"A comma separated string of attributes to sort by, "
                    f"each attribute must be prefixed with `+` for a descending "
                    f"sort or a `-` for an ascending sort. The accepted attribute "
                    f"names are: {all_fields}. For example `sorts=-{field_name_1},"
                    f"-{field_name_2}` will sort the {name} first by descending "
                    f"{field_name_1} and then ascending {field_name_2}. A sort"
                    f"parameter with multiple instances of the same sort attribute "
                    f"will respond with the ERROR_INVALID_SORT_ATTRIBUTE "
                    f"error.",
                ),
                OpenApiParameter(
                    name="page",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.INT,
                    description="Defines which page should be returned.",
                ),
                OpenApiParameter(
                    name="size",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.INT,
                    description=f"Defines how many {name} should be returned per "
                    f"page.",
                ),
            ],
            "responses": {
                200: serializer_class(many=True),
                400: get_error_schema(
                    [
                        "ERROR_PAGE_SIZE_LIMIT",
                        "ERROR_INVALID_PAGE",
                        "ERROR_INVALID_SORT_DIRECTION",
                        "ERROR_INVALID_SORT_ATTRIBUTE",
                    ]
                ),
                401: None,
            },
        }
