from django.urls import path, include

from baserow.core.registries import ApplicationType

from .models import Database
from .table.handler import TableHandler
from .api.v0 import urls as api_urls
from .api.v0.serializers import DatabaseSerializer


class DatabaseApplicationType(ApplicationType):
    type = 'database'
    model_class = Database
    instance_serializer_class = DatabaseSerializer

    def pre_delete(self, user, database):
        """
        When a database is deleted we must also delete the related tables via the table
        handler.
        """
        database_tables = database.table_set.all().select_related('database__group')
        table_handler = TableHandler()

        for table in database_tables:
            table_handler.delete_table(user, table)

    def get_api_v0_urls(self):
        return [
            path('database/', include(api_urls, namespace=self.type)),
        ]
