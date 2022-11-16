from django.db import connection, migrations

from tqdm import tqdm


def forward(apps, schema_editor):
    Table = apps.get_model("database", "Table")

    with connection.schema_editor() as tables_schema_editor:
        # We need to stop the transaction because we might need to lock a lot of tables
        # which could result in an out of memory exception.
        tables_schema_editor.atomic.__exit__(None, None, None)

        for table in tqdm(
            Table.objects.all().order_by("id").iterator(chunk_size=100),
            desc="Resetting the order of all tables.",
        ):
            table_name = f"database_table_{table.id}"
            tables_schema_editor.execute(
                f"""
                update {table_name} c1
                  set "order" = c2.seqnum from (
                    select c2.*, row_number() over (
                        ORDER BY c2."order", c2."id"
                    ) as seqnum from {table_name} c2
                  ) c2
                where c2.id = c1.id;
                """
            )


class Migration(migrations.Migration):

    dependencies = [
        ("database", "0091_view_show_logo"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
