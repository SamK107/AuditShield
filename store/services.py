from .models import DownloadToken


def deliver_order(order):
    """
    Active la livraison de l'actif après paiement réussi.
    - Crée un DownloadToken si possible.
    - Prévu pour extension (email, facture, etc.).
    """
    if order.status != order.PAID:
        return
    # Crée le token de téléchargement si le produit a un fichier
    if hasattr(order.product, "deliverable_file") and order.product.deliverable_file:
        DownloadToken.objects.get_or_create(order=order)
    # TODO: email, facture, etc. (extension future)
