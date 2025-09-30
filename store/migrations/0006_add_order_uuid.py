from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0005_paymentwebhooklog"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="uuid",
            field=models.UUIDField(null=True, blank=True, editable=False),
        ),
    ]
