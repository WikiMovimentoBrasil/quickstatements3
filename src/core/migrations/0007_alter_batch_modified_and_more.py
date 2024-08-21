# Generated by Django 5.0.7 on 2024-08-20 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_batchcommand_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batch',
            name='modified',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterIndexTogether(
            name='batchcommand',
            index_together={('batch', 'index')},
        ),
    ]