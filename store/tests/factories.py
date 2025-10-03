import uuid

import factory
from django.utils import timezone

from downloads.models import DownloadableAsset, DownloadCategory
from store.models import Order, Product


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    slug = factory.Sequence(lambda n: f"audit-sans-peur-{n}")
    title = factory.Sequence(lambda n: f"Audit Sans Peur #{n}")
    price_fcfa = 15000
    is_published = True


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    product = factory.SubFactory(ProductFactory)
    email = factory.Sequence(lambda n: f"buyer{n}@example.com")
    amount_fcfa = 15000
    transaction_id = factory.LazyFunction(lambda: f"txn_{uuid.uuid4().hex[:10]}")
    status = factory.LazyAttribute(
        lambda o: Order.STATUS_CHOICES[1][0] if hasattr(Order, "STATUS_CHOICES") else "pending"
    )
    created_at = factory.LazyFunction(timezone.now)


class DownloadCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DownloadCategory

    slug = factory.Sequence(lambda n: f"ebook-category-{n}")
    title = factory.Sequence(lambda n: f"Ebook Category {n}")
    page_path = factory.LazyAttribute(lambda o: f"/{o.slug}")


class DownloadableAssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DownloadableAsset

    category = factory.SubFactory(DownloadCategoryFactory)
    title = factory.Iterator(["PDF A4", "PDF 6x9"])
    file = factory.Sequence(lambda n: (f"ebooks/audit-sans-peur-{n}.pdf"))
    is_published = True
