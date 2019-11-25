# Generated by Django 2.2.4 on 2019-11-22 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documenten", "0009_auto_20191107_1028"),
    ]

    operations = [
        migrations.AlterField(
            model_name="enkelvoudiginformatieobjectcanonical",
            name="lock",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Hash string, wordt gebruikt als ID voor de lock",
                max_length=100,
            ),
        ),
    ]
