# Generated by Django 5.0.8 on 2024-09-19 17:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_batchcommand_response_json"),
    ]

    operations = [
        migrations.AddField(
            model_name="batchcommand",
            name="data_type_verified",
            field=models.BooleanField(default=False),
        ),
    ]