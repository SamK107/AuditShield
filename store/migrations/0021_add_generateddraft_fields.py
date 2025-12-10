# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0020_add_generateddraft_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="generateddraft",
            name="model_name",
            field=models.CharField(
                max_length=100,
                blank=True,
                default="",
                help_text="Modèle LLM utilisé (ex: gpt-4o-mini)",
            ),
        ),
        migrations.AddField(
            model_name="generateddraft",
            name="token_usage",
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text="Nombre de tokens utilisés",
            ),
        ),
        migrations.AddField(
            model_name="generateddraft",
            name="log",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Log de génération, prompt, debug info, etc.",
            ),
        ),
    ]

