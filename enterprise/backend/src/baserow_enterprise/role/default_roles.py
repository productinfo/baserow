from baserow.core.operations import (
    CreateApplicationsGroupOperationType,
    ListApplicationsGroupOperationType,
    ReadApplicationOperationType,
    ReadGroupOperationType,
    DeleteGroupOperationType,
    UpdateGroupOperationType,
    UpdateGroupOperationType,
    ListApplicationsGroupOperationType,
)


from baserow.contrib.database.operations import (
    ListTablesDatabaseTableOperationType,
    CreateTableDatabaseTableOperationType,
)

from baserow.contrib.database.table.operations import (
    ReadDatabaseTableOperationType,
    UpdateDatabaseTableOperationType,
    DeleteDatabaseTableOperationType,
    ListRowsDatabaseTableOperationType,
    CreateRowDatabaseTableOperationType,
)

from baserow.contrib.database.rows.operations import (
    ReadDatabaseRowOperationType,
    UpdateDatabaseRowOperationType,
    DeleteDatabaseRowOperationType,
)

default_roles = {
    "admin": [
        ReadGroupOperationType,
        UpdateGroupOperationType,
        DeleteGroupOperationType,
        ListApplicationsGroupOperationType,
        ListTablesDatabaseTableOperationType,
        CreateTableDatabaseTableOperationType,
        ReadApplicationOperationType,
        ReadDatabaseTableOperationType,
        UpdateDatabaseTableOperationType,
        DeleteDatabaseTableOperationType,
        ListRowsDatabaseTableOperationType,
        CreateRowDatabaseTableOperationType,
        ReadDatabaseRowOperationType,
        UpdateDatabaseRowOperationType,
        DeleteDatabaseRowOperationType,
    ],
    "builder": [
        ReadGroupOperationType,
        ListApplicationsGroupOperationType,
        ListTablesDatabaseTableOperationType,
        CreateTableDatabaseTableOperationType,
        ReadApplicationOperationType,
        ReadDatabaseTableOperationType,
        UpdateDatabaseTableOperationType,
        DeleteDatabaseTableOperationType,
        ListRowsDatabaseTableOperationType,
        CreateRowDatabaseTableOperationType,
        ReadDatabaseRowOperationType,
        UpdateDatabaseRowOperationType,
        DeleteDatabaseRowOperationType,
    ],
    "editor": [
        ReadGroupOperationType,
        ListApplicationsGroupOperationType,
        ListTablesDatabaseTableOperationType,
        ReadApplicationOperationType,
        ReadDatabaseTableOperationType,
        ListRowsDatabaseTableOperationType,
        CreateRowDatabaseTableOperationType,
        ReadDatabaseRowOperationType,
        UpdateDatabaseRowOperationType,
        DeleteDatabaseRowOperationType,
    ],
    "commenter": [
        ReadGroupOperationType,
        ListApplicationsGroupOperationType,
        ListTablesDatabaseTableOperationType,
        ReadApplicationOperationType,
        ReadDatabaseTableOperationType,
        ListRowsDatabaseTableOperationType,
        ReadDatabaseRowOperationType,
    ],
    "viewer": [
        ReadGroupOperationType,
        ListApplicationsGroupOperationType,
        ListTablesDatabaseTableOperationType,
        ReadApplicationOperationType,
        ReadDatabaseTableOperationType,
        ListRowsDatabaseTableOperationType,
        ReadDatabaseRowOperationType,
    ],
    "no_role": [],
}
