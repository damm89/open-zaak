# Generated by Django 2.2.4 on 2019-10-17 09:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("documenten", "0007_auto_20190918_0842"),
        ("zaken", "0005_auto_20190918_0826"),
    ]

    operations = [
        migrations.RenameField(
            model_name="zaakinformatieobject",
            old_name="informatieobject",
            new_name="_informatieobject",
        ),
        migrations.AlterUniqueTogether(
            name="zaakinformatieobject", unique_together={("zaak", "_informatieobject")}
        ),
    ]
