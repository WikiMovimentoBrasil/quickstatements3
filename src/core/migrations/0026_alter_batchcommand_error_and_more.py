# Generated by Django 5.0.9 on 2025-02-11 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_alter_batchcommand_error"),
    ]

    operations = [
        migrations.AlterField(
            model_name="batchcommand",
            name="error",
            field=models.TextField(
                blank=True,
                choices=[
                    ("op_not_implemented", "Operation not implemented"),
                    ("no_statements_property", "No statements for given property"),
                    ("no_statements_value", "No statements with given value"),
                    ("no_qualifiers", "No qualifiers with given value"),
                    ("no_reference_parts", "No reference parts with given value"),
                    ("sitelink_invalid", "The sitelink id is invalid"),
                    ("combining_failed", "The next command failed"),
                    ("api_user_error", "API returned a User error"),
                    ("api_server_error", "API returned a server error"),
                    ("last_not_evaluated", "LAST could not be evaluated."),
                ],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="batchcommand",
            name="operation",
            field=models.TextField(
                blank=True,
                choices=[
                    ("create_item", "Create item"),
                    ("create_property", "Create property"),
                    ("set_statement", "Set statement"),
                    ("create_statement", "Create statement"),
                    ("remove_statement_by_id", "Remove statement by id"),
                    ("remove_statement_by_value", "Remove statement by value"),
                    ("remove_qualifier", "Remove qualifier"),
                    ("remove_reference", "Remove reference"),
                    ("set_sitelink", "Set sitelink"),
                    ("set_label", "Set label"),
                    ("set_description", "Set description"),
                    ("remove_sitelink", "Remove sitelink"),
                    ("remove_label", "Remove label"),
                    ("remove_description", "Remove description"),
                    ("add_alias", "Add alias"),
                    ("remove_alias", "Remove alias"),
                ],
                null=True,
            ),
        ),
    ]
