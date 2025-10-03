from django.db import migrations

MAP = [
    ("bonus", True, "EBOOK_ASP"),
    ("checklists", True, "EBOOK_ASP"),
    ("outils-pratiques", True, "EBOOK_ASP"),
    ("irregularites", True, "EBOOK_ASP"),
]

def up(apps, schema_editor):
    Category = apps.get_model("downloads", "DownloadCategory")
    for slug, prot, sku in MAP:
        Category.objects.filter(slug=slug).update(is_protected=prot, required_sku=sku)

def down(apps, schema_editor):
    Category = apps.get_model("downloads", "DownloadCategory")
    for slug, _, _ in MAP:
        Category.objects.filter(slug=slug).update(is_protected=False, required_sku="")

class Migration(migrations.Migration):
    dependencies = [
        ("downloads", "0007_secure_categories_phase1"),
    ]
    operations = [
        migrations.RunPython(up, reverse_code=down),
    ]


