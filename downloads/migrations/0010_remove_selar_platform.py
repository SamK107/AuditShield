# Generated manually on 2025-10-21
# Remove Selar platform choice and update existing records

from django.db import migrations, models


def migrate_selar_to_other(apps, schema_editor):
    """
    Migrate any existing 'selar' platform records to 'other'
    """
    ExternalEntitlement = apps.get_model("downloads", "ExternalEntitlement")
    ExternalEntitlement.objects.filter(platform="selar").update(platform="other")


def reverse_migration(apps, schema_editor):
    """
    No reverse operation needed - selar records are now 'other'
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("downloads", "0009_externalentitlement"),
    ]

    operations = [
        # First, migrate existing data
        migrations.RunPython(migrate_selar_to_other, reverse_migration),
        
        # Then, update the field choices
        migrations.AlterField(
            model_name="externalentitlement",
            name="platform",
            field=models.CharField(
                choices=[
                    ("publiseer", "Publiseer"),
                    ("youscribe", "YouScribe Afrique"),
                    ("chariow", "Chariow"),
                    ("other", "Autre"),
                ],
                default="other",
                max_length=20,
            ),
        ),
    ]

