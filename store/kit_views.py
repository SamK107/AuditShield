# store/kit_views.py
"""
Vues pour le système de suivi des commandes Kit personnalisé.
"""
import logging
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from store.models import KitOrder

logger = logging.getLogger(__name__)


def kit_payment_success(request, tracking_id: str):
    """
    Page de confirmation après paiement réussi pour un Kit personnalisé.

    Args:
        tracking_id: L'ID de suivi (ex: KCP-00001)
    """
    kit_order = get_object_or_404(KitOrder, tracking_id=tracking_id)

    # S'assurer que le statut est PAYMENT_RECEIVED
    if kit_order.status != KitOrder.STATUS_PAYMENT_RECEIVED:
        # Si déjà traité, rediriger vers le tracking
        return redirect("store:kit_tracking", tracking_id=tracking_id)

    context = {
        "order": kit_order,
        "starter_pack_url": reverse("store:kit_starter_pack"),
    }

    return render(request, "store/kit_payment_success.html", context)


def kit_tracking(request, tracking_id: str):
    """
    Page de suivi de la commande Kit personnalisé.

    Args:
        tracking_id: L'ID de suivi (ex: KCP-00001)
    """
    kit_order = get_object_or_404(KitOrder, tracking_id=tracking_id)

    # Définir les étapes du processus
    steps = [
        {
            "code": KitOrder.STATUS_PAYMENT_RECEIVED,
            "title": "Paiement reçu",
            "description": "Votre paiement a été confirmé et enregistré.",
        },
        {
            "code": KitOrder.STATUS_ANALYSIS,
            "title": "Analyse des documents",
            "description": (
                "Nos experts analysent vos documents et préparent "
                "la structure de votre kit personnalisé."
            ),
        },
        {
            "code": KitOrder.STATUS_WRITING,
            "title": "Rédaction en cours",
            "description": (
                "Rédaction de votre kit personnalisé selon vos besoins "
                "et les meilleures pratiques d'audit."
            ),
        },
        {
            "code": KitOrder.STATUS_REVIEW,
            "title": "Relecture & consolidation",
            "description": (
                "Relecture approfondie et consolidation finale de votre "
                "kit avant livraison."
            ),
        },
        {
            "code": KitOrder.STATUS_DONE,
            "title": "Livraison finale",
            "description": (
                "Votre kit personnalisé est prêt et vous sera envoyé "
                "par email."
            ),
        },
    ]

    # Déterminer l'état de chaque étape
    status_order = [
        KitOrder.STATUS_PAYMENT_RECEIVED,
        KitOrder.STATUS_ANALYSIS,
        KitOrder.STATUS_WRITING,
        KitOrder.STATUS_REVIEW,
        KitOrder.STATUS_DONE,
    ]

    current_index = status_order.index(kit_order.status)

    for i, step in enumerate(steps):
        if i < current_index:
            step["state"] = "completed"
        elif i == current_index:
            step["state"] = "current"
        else:
            step["state"] = "pending"

    context = {
        "order": kit_order,
        "steps": steps,
    }

    return render(request, "store/kit_tracking.html", context)


def kit_starter_pack_view(request):
    """
    Vue pour télécharger le Starter Pack PDF.

    Le Starter Pack est un PDF statique disponible immédiatement
    après paiement.
    """
    # Chemin vers le fichier Starter Pack
    # Par défaut: BASE_DIR / "assets" / "starter_pack.pdf"
    starter_pack_path = Path(settings.BASE_DIR) / "assets" / "starter_pack.pdf"

    # Fallback: chercher dans STATIC_ROOT ou MEDIA_ROOT
    if not starter_pack_path.exists():
        if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
            starter_pack_path = Path(settings.STATIC_ROOT) / "starter_pack.pdf"
        elif hasattr(settings, "MEDIA_ROOT") and settings.MEDIA_ROOT:
            starter_pack_path = Path(settings.MEDIA_ROOT) / "starter_pack.pdf"

    if not starter_pack_path.exists():
        logger.error(
            f"[kit_starter_pack] Fichier introuvable: {starter_pack_path}"
        )
        raise Http404("Starter Pack non disponible pour le moment.")

    try:
        return FileResponse(
            open(starter_pack_path, "rb"),
            content_type="application/pdf",
            filename="starter_pack_audit_sans_peur.pdf",
        )
    except Exception as e:
        logger.exception(f"[kit_starter_pack] Erreur lecture fichier: {e}")
        raise Http404("Erreur lors du téléchargement du Starter Pack.")

