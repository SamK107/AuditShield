from django.db import migrations

PROTECTED = [
    ("bonus", True, "EBOOK_ASP"),
    ("checklists", True, "EBOOK_ASP"),
    ("outils-pratiques", True, "EBOOK_ASP"),
    ("irregularites", True, "EBOOK_ASP"),
]

def secure_cats(apps, schema_editor):
    Category = apps.get_model("downloads", "DownloadCategory")
    for slug, prot, sku in PROTECTED:
        Category.objects.filter(slug=slug).update(is_protected=prot, required_sku=sku)

def unsecure_cats(apps, schema_editor):
    Category = apps.get_model("downloads", "DownloadCategory")
    for slug, _, _ in PROTECTED:
        Category.objects.filter(slug=slug).update(is_protected=False, required_sku="")

class Migration(migrations.Migration):
    dependencies = [
        ("downloads", "0006_downloadcategory_is_protected_and_more"),
    ]

    operations = [
        migrations.RunPython(secure_cats, reverse_code=unsecure_cats),
    ]
