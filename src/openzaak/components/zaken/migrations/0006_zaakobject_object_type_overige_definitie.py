# Generated by Django 3.2.12 on 2022-04-27 15:58

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("zaken", "0005_auto_20220310_2216"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaakobject",
            name="object_type_overige_definitie",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True,
                help_text='Verwijzing naar het schema van het type OBJECT als `objectType` de waarde "overige" heeft.',
                null=True,
                verbose_name="definitie object type overige",
            ),
        ),
    ]
