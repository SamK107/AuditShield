import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0007_fill_order_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
