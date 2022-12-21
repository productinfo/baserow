from django.db.models import Q

from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.contrib.database.table.models import Table
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class DatabaseTableObjectScopeType(ObjectScopeType):
    type = "database_table"
    model_class = Table
    select_related = ["database", "database__group"]

    def get_parent_scope(self):
        return object_scope_type_registry.get("database")

    def get_parent(self, context):
        return context.database

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(database__group__in=[s.id for s in scopes])

        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(database__in=[s.id for s in scopes])

        return None
