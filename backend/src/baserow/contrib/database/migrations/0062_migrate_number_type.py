# Generated by Django 3.2.6 on 2022-02-14 13:26

from baserow.contrib.database.fields.models import NumberField
from django.db import migrations
from django.db.models import Q


def forward(apps, schema_editor):
    """
    If the NumberField.number_type was decimal we keep the decimal places
    intact.

    If the NumberField.number_type was integer we set the decimal places to
    0 as the number field could have any number of decimal places set before.
    """
    NumberField = apps.get_model("database", "NumberField")
    while NumberField.objects.filter(
        Q(number_type="INTEGER"), ~Q(number_decimal_places=0)
    ).exists():
        NumberField.objects.filter(number_type="INTEGER").update(
            number_decimal_places=0
        )


def reverse(apps, schema_editor):
    ...


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("database", "0061_change_decimal_places"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
