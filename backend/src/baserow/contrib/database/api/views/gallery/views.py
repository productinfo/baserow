from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import allowed_includes, map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.database.api.fields.errors import (
    ERROR_FIELD_DOES_NOT_EXIST,
    ERROR_FILTER_FIELD_NOT_FOUND,
    ERROR_ORDER_BY_FIELD_NOT_FOUND,
    ERROR_ORDER_BY_FIELD_NOT_POSSIBLE,
)
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_example_row_serializer_class,
    get_row_serializer_class,
)
from baserow.contrib.database.api.views.errors import (
    ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
    ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
    ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
)
from baserow.contrib.database.api.views.gallery.serializers import (
    GalleryViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.serializers import FieldOptionsField
from baserow.contrib.database.api.views.utils import get_public_view_authorization_token
from baserow.contrib.database.fields.exceptions import (
    FieldDoesNotExist,
    FilterFieldNotFound,
    OrderByFieldNotFound,
    OrderByFieldNotPossible,
)
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.exceptions import (
    NoAuthorizationToPubliclySharedView,
    ViewDoesNotExist,
    ViewFilterTypeDoesNotExist,
    ViewFilterTypeNotAllowedForField,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GalleryView
from baserow.contrib.database.views.registries import (
    view_filter_type_registry,
    view_type_registry,
)
from baserow.core.exceptions import UserNotInGroup
from baserow.core.handler import CoreHandler

from .errors import ERROR_GALLERY_DOES_NOT_EXIST
from .pagination import GalleryLimitOffsetPagination


class GalleryViewView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only rows that belong to the related view's "
                "table.",
            ),
            OpenApiParameter(
                name="count",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description="If provided only the count will be returned.",
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A comma separated list allowing the values of `field_options` "
                    "which will add the object/objects with the same name to the "
                    "response if included. The `field_options` object contains user "
                    "defined view settings for each field. For example the field's "
                    "order is included in here."
                ),
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `limit` "
                "parameter and defines from which offset the rows should "
                "be returned.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided only rows with data that matches the search "
                "query are going to be returned.",
            ),
        ],
        tags=["Database table gallery view"],
        operation_id="list_database_table_gallery_view_rows",
        description=(
            "Lists the requested rows of the view's table related to the provided "
            "`view_id` if the authorized user has access to the database's group. "
            "The response is paginated by a limit/offset style."
        ),
        responses={
            200: get_example_pagination_serializer_class(
                get_example_row_serializer_class(
                    example_type="get", user_field_names=False
                ),
                additional_fields={
                    "field_options": FieldOptionsField(
                        serializer_class=GalleryViewFieldOptionsSerializer,
                        required=False,
                    ),
                },
                serializer_name="PaginationSerializerWithGalleryViewFieldOptions",
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GALLERY_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GALLERY_DOES_NOT_EXIST,
        }
    )
    @allowed_includes("field_options")
    def get(self, request: Request, view_id: int, field_options: bool):
        """Lists the rows for the gallery view."""

        view_handler = ViewHandler()
        view = view_handler.get_view(request.user, view_id, GalleryView)
        view_type = view_type_registry.get_by_model(view)

        group = view.table.database.group
        CoreHandler().check_permissions(
            request.user,
            ListRowsDatabaseTableOperationType.type,
            group=group,
            context=view.table,
            allow_if_template=True,
        )

        search = request.GET.get("search")

        model = view.table.get_model()
        queryset = view_handler.get_queryset(view, search, model)

        if "count" in request.GET:
            return Response({"count": queryset.count()})

        paginator = GalleryLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True
        )
        serializer = serializer_class(page, many=True)

        response = paginator.get_paginated_response(serializer.data)

        if field_options:
            context = {"fields": [o["field"] for o in model._field_objects.values()]}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.data.update(**serializer_class(view, context=context).data)

        return response


class PublicGalleryViewRowsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns only rows that belong to the related view.",
            ),
            OpenApiParameter(
                name="count",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description="If provided only the count will be returned.",
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A comma separated list allowing the values of "
                    "`field_options` which will add the object/objects with the "
                    "same "
                    "name to the response if included. The `field_options` object "
                    "contains user defined view settings for each field. For "
                    "example the field's width is included in here."
                ),
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `limit` "
                "parameter and defines from which offset the rows should "
                "be returned.",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines which page of rows should be returned. Either "
                "the `page` or `limit` can be provided, not both.",
            ),
            OpenApiParameter(
                name="size",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `page` parameter "
                "and defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided only rows with data that matches the search "
                "query are going to be returned.",
            ),
            OpenApiParameter(
                name="order_by",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Optionally the rows can be ordered by provided field ids "
                "separated by comma. By default a field is ordered in ascending (A-Z) "
                "order, but by prepending the field with a '-' it can be ordered "
                "descending (Z-A).",
            ),
            OpenApiParameter(
                name="filter__{field}__{filter}",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    f"The rows can optionally be filtered by the same view filters "
                    f"available for the views. Multiple filters can be provided if "
                    f"they follow the same format. The field and filter variable "
                    f"indicate how to filter and the value indicates where to filter "
                    f"on.\n\n"
                    f"For example if you provide the following GET parameter "
                    f"`filter__field_1__equal=test` then only rows where the value of "
                    f"field_1 is equal to test are going to be returned.\n\n"
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                ),
            ),
            OpenApiParameter(
                name="filter_type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "`AND`: Indicates that the rows must match all the provided "
                    "filters.\n"
                    "`OR`: Indicates that the rows only have to match one of the "
                    "filters.\n\n"
                    "This works only if two or more filters are provided."
                ),
            ),
            OpenApiParameter(
                name="include_fields",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "All the fields are included in the response by default. You can "
                    "select a subset of fields by providing the fields query "
                    "parameter. If you for example provide the following GET "
                    "parameter `include_fields=field_1,field_2` then only the fields "
                    "with id `1` and id `2` are going to be selected and included in "
                    "the response."
                ),
            ),
            OpenApiParameter(
                name="exclude_fields",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "All the fields are included in the response by default. You can "
                    "select a subset of fields by providing the exclude_fields query "
                    "parameter. If you for example provide the following GET "
                    "parameter `exclude_fields=field_1,field_2` then the fields with "
                    "id `1` and id `2` are going to be excluded from the selection and "
                    "response. "
                ),
            ),
        ],
        tags=["Database table gallery view"],
        operation_id="public_list_database_table_gallery_view_rows",
        description=(
            "Lists the requested rows of the view's table related to the provided "
            "`slug` if the gallery view is public."
            "The response is paginated either by a limit/offset or page/size style. "
            "The style depends on the provided GET parameters. The properties of the "
            "returned rows depends on which fields the table has. For a complete "
            "overview of fields use the **list_database_table_fields** endpoint to "
            "list them all. In the example all field types are listed, but normally "
            "the number in field_{id} key is going to be the id of the field. "
            "The value is what the user has provided and the format of it depends on "
            "the fields type.\n"
            "\n"
        ),
        responses={
            200: get_example_pagination_serializer_class(
                get_example_row_serializer_class(
                    example_type="get", user_field_names=False
                ),
                additional_fields={
                    "field_options": FieldOptionsField(
                        serializer_class=GalleryViewFieldOptionsSerializer,
                        required=False,
                    ),
                },
                serializer_name="PublicPaginationSerializerWithGalleryViewFieldOptions",
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            401: get_error_schema(["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"]),
            404: get_error_schema(
                ["ERROR_GALLERY_DOES_NOT_EXIST", "ERROR_FIELD_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GALLERY_DOES_NOT_EXIST,
            OrderByFieldNotFound: ERROR_ORDER_BY_FIELD_NOT_FOUND,
            OrderByFieldNotPossible: ERROR_ORDER_BY_FIELD_NOT_POSSIBLE,
            FilterFieldNotFound: ERROR_FILTER_FIELD_NOT_FOUND,
            ViewFilterTypeDoesNotExist: ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
            ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            NoAuthorizationToPubliclySharedView: ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
        }
    )
    @transaction.atomic
    @allowed_includes("field_options")
    def get(self, request: Request, slug: str, field_options: bool) -> Response:
        """
        Lists all the rows of a gallery view, paginated with
        GalleryLimitOffsetPagination.

        Optionally the field options can also be included in the response if the the
        `field_options` are provided in the include GET parameter.
        """

        search = request.GET.get("search")
        order_by = request.GET.get("order_by")
        include_fields = request.GET.get("include_fields")
        exclude_fields = request.GET.get("exclude_fields")
        filter_type = (
            FILTER_TYPE_OR
            if request.GET.get("filter_type", "AND").upper() == "OR"
            else FILTER_TYPE_AND
        )
        filter_object = {key: request.GET.getlist(key) for key in request.GET.keys()}
        count = "count" in request.GET

        view_handler = ViewHandler()
        view = view_handler.get_public_view_by_slug(
            request.user,
            slug,
            GalleryView,
            authorization_token=get_public_view_authorization_token(request),
        )
        view_type = view_type_registry.get_by_model(view)
        model = view.table.get_model()

        (
            queryset,
            field_ids,
            publicly_visible_field_options,
        ) = ViewHandler().get_public_rows_queryset_and_field_ids(
            view,
            search=search,
            order_by=order_by,
            include_fields=include_fields,
            exclude_fields=exclude_fields,
            filter_type=filter_type,
            filter_object=filter_object,
            table_model=model,
            view_type=view_type,
        )

        if count:
            return Response({"count": queryset.count()})

        paginator = GalleryLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request, self)

        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True, field_ids=field_ids
        )
        serializer = serializer_class(page, many=True)

        response = paginator.get_paginated_response(serializer.data)

        if field_options:
            context = {"field_options": publicly_visible_field_options}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.data.update(**serializer_class(view, context=context).data)

        return response
