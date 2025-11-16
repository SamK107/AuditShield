from __future__ import annotations

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from .models import ClientInquiry, GeneratedDraft


@staff_member_required
@require_GET
def kit_complete_processing_list(request):
    """
    Backoffice: liste les demandes Kit complétées/payées et en cours de traitement.
    """
    STATI = {"PAID", "IA_RUNNING", "DRAFT_DONE", "FINAL_UPLOADED", "PUBLISHED"}
    inquiries = (
        ClientInquiry.objects.filter(
            kind=ClientInquiry.KIND_KIT,
            processing_state__in=STATI,
        )
        .order_by("-created_at")
    )
    return render(request, "store/kit_complete_processing.html", {"inquiries": inquiries})


def _run_kit_ai_generation_sync(inquiry: ClientInquiry) -> None:
    """
    Lance la génération DOCX via la tâche existante.
    Utilise Celery si disponible; sinon, exécute en synchrone.
    """
    try:
        from .tasks import build_kit_word
        try:
            # Si Celery est opérationnel
            build_kit_word.delay(inquiry.id)
        except Exception:
            # Fallback synchrone
            build_kit_word(inquiry.id)
    except Exception as e:
        raise e


@staff_member_required
@require_POST
def kit_complete_process(request, pk: int):
    inquiry = get_object_or_404(ClientInquiry, pk=pk, kind=ClientInquiry.KIND_KIT)
    if inquiry.payment_status != "PAID":
        messages.error(request, "Paiement non confirmé pour cette demande.")
        return redirect("store:kit_complete_processing")

    if inquiry.processing_state not in ("PAID", "IA_RUNNING"):
        messages.warning(request, "État actuel incompatible avec le lancement du traitement.")
        return redirect("store:kit_complete_processing")

    # Marque IA_RUNNING et lance
    inquiry.processing_state = "IA_RUNNING"
    inquiry.save(update_fields=["processing_state"])
    try:
        _run_kit_ai_generation_sync(inquiry)
        messages.success(request, "Traitement IA lancé. Actualisez dans quelques instants.")
    except Exception as e:
        messages.error(request, f"Erreur lors du lancement du traitement IA: {e}")
        inquiry.processing_state = "PAID"
        inquiry.save(update_fields=["processing_state"])
    return redirect("store:kit_complete_processing")


@staff_member_required
@require_POST
def kit_complete_upload(request, pk: int):
    inquiry = get_object_or_404(ClientInquiry, pk=pk, kind=ClientInquiry.KIND_KIT)
    if inquiry.processing_state not in ("DRAFT_DONE", "FINAL_UPLOADED"):
        messages.error(request, "Le brouillon IA doit d'abord être prêt (DRAFT_DONE).")
        return redirect("store:kit_complete_processing")
    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("Fichier manquant.")
    # Accepter .docx / .pdf
    allowed = (".docx", ".pdf")
    name_l = (f.name or "").lower()
    if not any(name_l.endswith(ext) for ext in allowed):
        messages.error(request, "Format non pris en charge (acceptez .docx ou .pdf).")
        return redirect("store:kit_complete_processing")
    # Sauvegarde dans human_pdf si PDF; sinon dans GeneratedDraft.docx
    if name_l.endswith(".pdf"):
        inquiry.human_pdf.save(f.name, f, save=True)
        inquiry.processing_state = "FINAL_UPLOADED"
        inquiry.save(update_fields=["human_pdf", "processing_state"])
    else:
        draft, _ = GeneratedDraft.objects.get_or_create(inquiry=inquiry)
        draft.docx.save(f.name, f, save=True)
        inquiry.processing_state = "FINAL_UPLOADED"
        inquiry.save(update_fields=["processing_state"])
    messages.success(request, "Version validée uploadée.")
    return redirect("store:kit_complete_processing")


@staff_member_required
@require_POST
def kit_complete_publish(request, pk: int):
    inquiry = get_object_or_404(ClientInquiry, pk=pk, kind=ClientInquiry.KIND_KIT)
    if inquiry.processing_state != "FINAL_UPLOADED":
        messages.error(request, "Téléchargez d'abord la version finalisée.")
        return redirect("store:kit_complete_processing")
    # Lien de téléchargement absolu
    file_url = None
    if inquiry.human_pdf:
        file_url = request.build_absolute_uri(inquiry.human_pdf.url)
    elif getattr(inquiry, "generated_draft", None) and inquiry.generated_draft.docx:
        file_url = request.build_absolute_uri(inquiry.generated_draft.docx.url)
    if not file_url:
        messages.error(request, "Aucun fichier final disponible pour l'envoi.")
        return redirect("store:kit_complete_processing")
    # Envoi email simple
    subject = "Votre Kit complet de préparation à l’audit"
    body = (
        f"Bonjour {inquiry.contact_name or ''},\n\n"
        f"Votre document est prêt. Téléchargez-le ici : {file_url}\n\n"
        f"Bien cordialement,\nAuditSansPeur"
    )
    try:
        EmailMessage(subject=subject, body=body, to=[inquiry.email]).send(fail_silently=False)
    except Exception as e:
        messages.error(request, f"Erreur d'envoi email: {e}")
        return redirect("store:kit_complete_processing")
    # Mettre à jour l'état visuel
    inquiry.processing_state = "PUBLISHED"
    # Si vous avez un champ published_at ailleurs, ajustez ici; on garde simple
    inquiry.save(update_fields=["processing_state"])
    messages.success(request, "Document publié et email envoyé au client.")
    return redirect("store:kit_complete_processing")


