from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional
from xmlrpc.client import Boolean # TODO:
from django.db.models import QuerySet, Q

from baserow.core.exceptions import (
    ApplicationTypeAlreadyRegistered,
    ApplicationTypeDoesNotExist,
    AuthenticationProviderTypeAlreadyRegistered,
    AuthenticationProviderTypeDoesNotExist,
    ObjectScopeTypeAlreadyRegistered,
    ObjectScopeTypeDoesNotExist,
    OperationTypeAlreadyRegistered,
    OperationTypeDoesNotExist,
    PermissionDenied,
    PermissionManagerTypeAlreadyRegistered,
    PermissionManagerTypeDoesNotExist,
)
from baserow.core.registries import (
    OperationType,
    PermissionManagerType,
    operation_type_registry,
)
from baserow.contrib.database.views.operations import (
    CreateViewFilterOperationType,
    CreateViewOperationType,
    CreateViewSortOperationType,
    DeleteViewDecorationOperationType,
    DeleteViewFilterOperationType,
    DeleteViewOperationType,
    DeleteViewSortOperationType,
    DuplicateViewOperationType,
    OrderViewsOperationType,
    ReadViewFilterOperationType,
    ReadViewOperationType,
    ReadViewsOrderOperationType,
    ReadViewSortOperationType,
    UpdateViewFieldOptionsOperationType,
    UpdateViewFilterOperationType,
    UpdateViewOperationType,
    UpdateViewSlugOperationType,
    UpdateViewSortOperationType,
)
from baserow.contrib.database.views.models import View, OWNERSHIP_TYPE_COLLABORATIVE
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.license.features import PREMIUM


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from .models import Group


# TODO: bypass public views

class ViewOwnershipPermissionManagerType(PermissionManagerType):
    """
    A permission manager is responsible to permit or disallow a specific operation
    according to the given context.

    A permission manager is also responsible to generate the data sent to the
    frontend to make it check the permission.

    And finally, a permission manager can filter the list querysets
    to remove disallowed objects from this list.

    See each PermissionManager method and `CoreHandler` methods for more details.
    """

    type = "view_ownership"

    def check_permissions(
        self,
        actor: "AbstractUser",
        operation_name: str,
        group: Optional["Group"] = None,
        context: Optional[Any] = None,
        include_trash: Boolean = False,
    ) -> Optional[Boolean]:
        """
        This method is called each time a permission on an operation is checked by the
        `CoreHandler().check_permissions()` method if the current permission manager is
        listed in the `settings.PERMISSION_MANAGERS` list.

        It should:
            - return `True` if the operation is permitted given the other parameters
            - raise a `PermissionDenied` exception if the operation is disallowed
            - return `None` if the condition required by the permission manager are not
              met.

        By default, this method raises a PermissionDenied exception.

        :param actor: The actor who wants to execute the operation. Generally a `User`,
            but can be a `Token`.
        :param operation_name: The operation name the actor wants to execute.
        :param group: The optional group in which  the operation takes place.
        :param context: The optional object affected by the operation. For instance
            if you are updating a `Table` object, the context is this `Table` object.
        :param include_trash: If true then also checks if the given group has been
            trashed instead of raising a DoesNotExist exception.
        :raise PermissionDenied: If the operation is disallowed a PermissionDenied is
            raised.
        :return: `True` if the operation is permitted, None if the permission manager
            can't decide.
        """


        operation_type = operation_type_registry.get(operation_name)
        print(operation_name)

        if operation_name != "database.table.view.read" and operation_name != "database.table.view.duplicate":
            return True

        if not group:
            return
        
        if not context:
            return

        premium = LicenseHandler.user_has_feature(PREMIUM, actor, group)

        if premium:
            if context.ownership_type == OWNERSHIP_TYPE_COLLABORATIVE:
                return True
            if context.ownership_type == "personal" and context.created_by == actor:
                return True
            raise PermissionDenied()
        else:
            if context.ownership_type != OWNERSHIP_TYPE_COLLABORATIVE:
                raise PermissionDenied()

        return True

    # def get_permissions_object(
    #     self, actor: "AbstractUser", group: Optional["Group"] = None
    # ) -> Any:
    #     """
    #     This method should return the data necessary to easily check a permission from
    #     a client. This object can be used for instance from the frontend to hide or
    #     show UI element accordingly to the user permissions.
    #     The data set returned must contain all the necessary information to prevent and
    #     the client shouldn't have to get more data to decide.

    #     This method is called when the `CoreHandler().get_permissions()` is called,
    #     if the permission manager is listed in the `settings.PERMISSION_MANAGERS`.
    #     It can return `None` if this permission manager is not relevant for the given
    #     actor/group for some reason.

    #     By default this method returns None.

    #     :param actor: The actor whom we want to compute the permission object for.
    #     :param group: The optional group into which we want to compute the permission
    #         object.
    #     :return: The permission object or None.
    #     """

    #     return None

    def filter_queryset(
        self,
        actor: "AbstractUser",
        operation_name: str,
        queryset: QuerySet,
        group: Optional["Group"] = None,
        context: Optional[Any] = None,
    ) -> QuerySet:
        """
        This method allows a permission manager to filter a given queryset accordingly
        to the actor permissions in the specified context. The
        `CoreHandler().filter_queryset()` method calls each permission manager listed in
        `settings.PERMISSION_MANAGERS` to successively filter the given queryset.

        :param actor: The actor whom we want to filter the queryset for.
            Generally a `User` but can be a Token.
        :param operation: The operation name for which we want to filter the queryset
            for.
        :param group: An optional group into which the operation takes place.
        :param context: An optional context object related to the current operation.
        :return: The queryset potentially filtered.
        """

        if not group:
            raise PermissionDenied()

        premium = LicenseHandler.user_has_feature(PREMIUM, actor, group)

        if premium:
            return queryset.filter(Q(ownership_type=OWNERSHIP_TYPE_COLLABORATIVE) | (Q(ownership_type="personal") & Q(created_by=actor)))
        else:
            return queryset.filter(ownership_type=OWNERSHIP_TYPE_COLLABORATIVE)
