from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("downloads", "0010_remove_selar_platform"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalentitlement",
            name="message_id",
            field=models.CharField(
                max_length=255,
                blank=True,
                null=True,
                unique=True,
                help_text="Message-ID IMAP pour idempotence",
            ),
        ),
        migrations.AddField(
            model_name="externalentitlement",
            name="sku",
            field=models.CharField(
                max_length=64,
                blank=True,
                null=True,
                help_text="Code produit (ex: EBOOK_ASP)",
            ),
        ),
        migrations.AddField(
            model_name="externalentitlement",
            name="raw_payload",
            field=models.TextField(
                blank=True, null=True, help_text="Brut email parsé (en-têtes + extrait)"
            ),
        ),
        migrations.AddField(
            model_name="externalentitlement",
            name="processed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]


