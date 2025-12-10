# Generated manually
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0019_add_kitorder_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="generateddraft",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now,
                help_text="Date de création du brouillon",
            ),
            preserve_default=False,
        ),
    ]

