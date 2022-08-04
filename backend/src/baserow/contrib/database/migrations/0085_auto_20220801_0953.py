# Generated by Django 3.2.13 on 2022-08-01 09:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0084_duplicatetablejob'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollaboratorField',
            fields=[
                ('field_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='database.field')),
            ],
            options={
                'abstract': False,
            },
            bases=('database.field',),
        ),
        migrations.AlterField(
            model_name='fileimportjob',
            name='name',
            field=models.CharField(default='', help_text='The name the created table.', max_length=255),
        ),
    ]