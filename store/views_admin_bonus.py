# store/views_admin_bonus.py
from __future__ import annotations

# --- Django & stdlib imports
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from io import BytesIO
from typing import List, Dict

from django.core.mail import EmailMessage
from django.urls import reverse

# --- Projet
from .models import BonusRequest
from .services.kit_builder import (
    build_docx_cover_and_guard,
    build_docx_content,
)

# python-docx
from docx import Document


# ======================================================================================
#                               VUES ADMIN — BONUS KIT
# ======================================================================================

@staff_member_required
@require_GET
def bonus_admin_list(request):
    """
    Liste des BonusRequest avec recherche (q), filtre de statut (status),
    tri rudimentaire (order), et pagination.
    """
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().upper()
    order = request.GET.get("order", "-created_at").strip() or "-created_at"
    page_number = request.GET.get("page", "1")

    qs = BonusRequest.objects.all()

    if q:
        # On cherche sur purchaser_name, delivery_email et notes si elles existent
        from django.db.models import Q
        qs = qs.filter(
            Q(purchaser_name__icontains=q) |
            Q(delivery_email__icontains=q) |
            Q(notes__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)

    # Sécurise l'order (colonne attendue). On tolère quelques champs standard.
    allowed_orders = {"created_at", "-created_at", "updated_at", "-updated_at", "status", "-status", "purchaser_name", "-purchaser_name"}
    if order not in allowed_orders:
        order = "-created_at"

    qs = qs.order_by(order)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(page_number)

    ctx = {
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "order": order,
        "total": paginator.count,
    }
    return render(request, "store/bonus_admin_list.html", ctx)


@staff_member_required
@require_GET
def bonus_admin_detail(request, pk: int):
    """
    Page de détail d’une demande. Affiche les métadonnées et les actions disponibles.
    """
    br = get_object_or_404(BonusRequest, pk=pk)
    ctx = {
        "br": br,
        "can_download": bool(br.docx_path),
        "can_generate": True,   # On autorise la génération/régénération à tout moment
        "can_mark_sent": (br.status in {"DRAFTED", "READY", "GENERATED"}),  # adaptez selon vos statuts
    }
    return render(request, "store/bonus_admin_detail.html", ctx)


# --------------------------------------------------------------------------------------
#                                  ACTIONS (POST)
# --------------------------------------------------------------------------------------

@staff_member_required
@require_POST
def bonus_admin_generate(request, pk: int):
    """
    Génère (ou régénère) le fichier DOCX du kit pour la demande donnée.
    - Construit la couverture/feuille de garde
    - Injecte le contenu (intro, Q/R, irrégularités)
    - Sauve dans le FileField `docx_path`
    - Met à jour le statut -> DRAFTED
    """
    br = get_object_or_404(BonusRequest, pk=pk)

    # 1) Construire le document
    doc = Document()
    build_docx_cover_and_guard(doc, br.purchaser_name, br.delivery_email)

    # 2) Préparer contenu
    intro_md, qas_list, irregularities_rows = _build_default_content(br)

    # 3) Injecter le contenu métier
    build_docx_content(doc, intro_md, qas_list, irregularities_rows)

    # 4) Sauvegarder en mémoire puis dans le FileField
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    filename = f"kit_{br.pk}.docx"
    br.docx_path.save(filename, ContentFile(buf.read()), save=False)

    # 5) Mettre à jour le statut
    br.status = "DRAFTED"
    br.save(update_fields=["docx_path", "status", "updated_at"])

    messages.success(request, "Le kit DOCX a été généré avec succès.")
    return redirect("store:bonus_admin_detail", pk=br.pk)


@staff_member_required
@require_POST
def bonus_admin_delete_docx(request, pk: int):
    """
    Supprime le fichier DOCX généré et remet le statut à 'NEW' (ou 'RECEIVED').
    """
    br = get_object_or_404(BonusRequest, pk=pk)
    if not br.docx_path:
        messages.info(request, "Aucun fichier à supprimer.")
        return redirect("store:bonus_admin_detail", pk=br.pk)

    # Supprime le fichier du storage
    br.docx_path.delete(save=False)
    br.docx_path = None
    # Remettre un statut initial cohérent selon votre workflow
    br.status = "NEW"
    br.save(update_fields=["docx_path", "status", "updated_at"])
    messages.success(request, "Le fichier généré a été supprimé.")
    return redirect("store:bonus_admin_detail", pk=br.pk)


@staff_member_required
def bonus_admin_download_docx(request, pk: int):
    """
    Téléchargement du fichier DOCX (GET uniquement).
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    br = get_object_or_404(BonusRequest, pk=pk)
    if not br.docx_path:
        raise Http404("Fichier introuvable.")

    # FileResponse utilisera le storage du FileField
    return FileResponse(
        br.docx_path.open("rb"),
        as_attachment=True,
        filename=br.docx_path.name.rsplit("/", 1)[-1] or f"kit_{br.pk}.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@staff_member_required
@require_POST
def bonus_admin_mark_sent(request, pk: int):
    """
    Marque la demande comme envoyée au client (statut 'SENT').
    """
    br = get_object_or_404(BonusRequest, pk=pk)
    if not br.docx_path:
        messages.warning(request, "Générez d’abord le DOCX avant de marquer comme envoyé.")
        return redirect("store:bonus_admin_detail", pk=br.pk)

    br.status = "SENT"
    br.save(update_fields=["status", "updated_at"])
    messages.success(request, "Statut mis à jour : la demande est marquée comme envoyée.")
    return redirect("store:bonus_admin_detail", pk=br.pk)


# ======================================================================================
#                                HELPERS (contenu)
# ======================================================================================

def _build_default_content(br: BonusRequest) -> tuple[str, List[Dict], List[List[str]]]:
    """
    Construit un contenu par défaut si vous n’avez pas (encore) branché d’IA
    ou d’analyse des fichiers .md / upload.

    Retourne:
      - intro_md: str (Markdown ou texte simple)
      - qas_list: List[dict] avec clés:
            question, good, partial, avoid, tip
      - irregularities_rows: List[List[str]] (tableau simple)
    """
    intro_md = (
        f"Ce kit personnalisé est préparé pour **{br.purchaser_name}** "
        f"(<{br.delivery_email}>). Il présente les notions clés, précautions et "
        f"conséquences pratiques afin de réussir la préparation à l’audit.\n\n"
        f"**Objectifs :** clarifier le périmètre, éviter les erreurs récurrentes, "
        f"et sécuriser la conformité documentaire et financière."
    )

    # Exemple minimal de 5 Q/R — Remplacez par 20 pour votre livrable final
    qas_list = [
        {
            "question": "Les rapprochements bancaires sont-ils réalisés mensuellement ?",
            "good": "Rapprochements mensuels signés par DFM et ordonnateur, écarts justifiés.",
            "partial": "Rapprochements irréguliers ou écarts non totalement documentés.",
            "avoid": "Aucun rapprochement, ou écarts laissés sans traitement.",
            "tip": "Mettre en place un calendrier mensuel, check-list, et un archivage standardisé.",
        },
        {
            "question": "Les dépenses respectent-elles les crédits disponibles ?",
            "good": "Contrôle systématique des crédits avant engagement.",
            "partial": "Quelques dépassements corrigés a posteriori.",
            "avoid": "Engagements et ordonnancements hors crédits.",
            "tip": "Activer des contrôles budgétaires et des alertes sur dépassements.",
        },
        {
            "question": "La piste d’audit des pièces justificatives est-elle complète ?",
            "good": "Pièces classées, paraphées, référencées ; chainage clair.",
            "partial": "Manques sporadiques, classement non homogène.",
            "avoid": "Absence de pièces clés, pièces non conformes.",
            "tip": "Adopter des modèles uniques et former les agents au classement.",
        },
        {
            "question": "Les immobilisations sont-elles inventoriées et rapprochées ?",
            "good": "Inventaire physique annuel, rapprochement compta/patrimoine.",
            "partial": "Inventaire partiel, fiches incomplètes.",
            "avoid": "Aucun inventaire, immobilisations non tracées.",
            "tip": "Mettre à jour le registre et apposer des étiquettes d’actifs.",
        },
        {
            "question": "Les procédures d’achat respectent-elles le code en vigueur ?",
            "good": "Dossiers complets (DAO, PV, contrats), seuils et modes respectés.",
            "partial": "Manques mineurs corrigés lors des contrôles.",
            "avoid": "Attributions sans concurrence ni justification.",
            "tip": "Utiliser des checklists par seuil/procédure et valider en amont.",
        },
    ]

    # 10 lignes d’irrégularités types (à adapter à votre référentiel)
    irregularities_rows = [
        ["Trésorerie", "Absence de rapprochements bancaires mensuels", "Écarts non détectés, risques de fraude"],
        ["Budget", "Engagements hors crédits disponibles", "Dépassements, observations récurrentes"],
        ["Achats", "Non-respect des seuils de mise en concurrence", "Risque d’irrégularité et d’annulation"],
        ["Patrimoine", "Inventaire physique non réalisé", "Actifs non tracés, pertes possibles"],
        ["Pièces Just.", "Dossiers incomplets (absence de PJ clés)", "Non-conformité, rejets du contrôle"],
        ["Recettes", "Mauvais rattachement des produits", "Image fidèle compromise"],
        ["Charges", "Absence de pièces probantes", "Rejets, corrections et redressements"],
        ["Paie", "Bulletins non conformes / absences de visas", "Risques sociaux et financiers"],
        ["Taxes", "Déclarations tardives / inexactes", "Pénalités et intérêts"],
        ["Clôture", "Absence de circularisation/lettrage", "Anomalies non identifiées"],
    ]

    return intro_md, qas_list, irregularities_rows



@staff_member_required
def mark_ready_and_send(request, pk):
    br = get_object_or_404(BonusRequest, pk=pk)
    # si conversion auto: ensure br.pdf_path
    # sinon, après upload manuel du PDF via l’admin, tu passes READY
    if not br.pdf_path:
        # fallback: si DOCX only, tu peux envoyer DOCX (ou bloquer)
        messages.error(request, "Ajoute le PDF avant l’envoi.")
        return redirect("store:bonus_admin_detail", pk=pk)

    # lien de téléchargement
    download_url = request.build_absolute_uri(reverse("store:download_bonus_pdf", args=[br.pk]))
    EmailMessage(
        subject="Votre Kit de préparation à l’audit — Bloom Shield Gouvernance",
        body=f"Bonjour {br.purchaser_name},\n\nVotre kit est prêt : {download_url}\n\nBien cordialement,\nBloom Shield Gouvernance",
        to=[br.delivery_email],
    ).send(fail_silently=False)

    br.status = "SENT"; br.save()
    messages.success(request, "Email envoyé au client.")
    return redirect("store:bonus_admin_detail", pk=pk)
    
# ======================================================================================
#                     SUGGESTION D’URLS (à placer dans store/urls.py)
# ======================================================================================
#
# from django.urls import path
# from . import views_admin_bonus as bonus_admin
#
# app_name = "store"
# urlpatterns = [
#     path("admin/bonus/", bonus_admin.bonus_admin_list, name="bonus_admin_list"),
#     path("admin/bonus/<int:pk>/", bonus_admin.bonus_admin_detail, name="bonus_admin_detail"),
#     path("admin/bonus/<int:pk>/generate/", bonus_admin.bonus_admin_generate, name="bonus_admin_generate"),
#     path("admin/bonus/<int:pk>/download/", bonus_admin.bonus_admin_download_docx, name="bonus_admin_download"),
#     path("admin/bonus/<int:pk>/mark-sent/", bonus_admin.bonus_admin_mark_sent, name="bonus_admin_mark_sent"),
#     path("admin/bonus/<int:pk>/delete-docx/", bonus_admin.bonus_admin_delete_docx, name="bonus_admin_delete_docx"),
# ]
#
# ======================================================================================
#                     NOTES INTÉGRATION / TEMPLATES MINIMAUX
# ======================================================================================
#
# - Templates attendus :
#   * store/bonus_admin_list.html
#   * store/bonus_admin_detail.html
#
# - Statuts BonusRequest (exemple usuel) :
#   NEW -> DRAFTED -> SENT
#   Adaptez les noms à vos Choices du modèle.
#
# - Modèle BonusRequest (champs utilisés ici) :
#   purchaser_name: CharField
#   delivery_email: EmailField
#   notes: TextField (optionnel)
#   status: CharField(choices=...)
#   docx_path: FileField(null=True, blank=True, upload_to="bonus_kits/")
#   created_at / updated_at: DateTimeField
#
# - Sécurité :
#   Toutes les vues sont décorées avec @staff_member_required.
#   Les actions qui modifient l’état sont en POST uniquement.
#
# - Personnalisation du contenu :
#   Remplacez _build_default_content par un branchement sur votre pipeline
#   (résumés .md, analyse de fichiers uploadés, génération IA, etc.).
#
