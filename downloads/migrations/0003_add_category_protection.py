from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("downloads", "0002_downloadcategory_remove_assetevent_asset_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="downloadcategory",
            name="is_protected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="downloadcategory",
            name="required_sku",
            field=models.CharField(max_length=64, blank=True),
        ),
    ]
