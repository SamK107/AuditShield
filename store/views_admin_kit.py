from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from .models import ClientInquiry, GeneratedDraft, InquiryDocument

logger = logging.getLogger(__name__)


@staff_member_required
@require_GET
def kit_complete_processing_list(request):
    """
    Backoffice: liste les demandes Kit complétées/payées et en cours de traitement.
    """
    STATI = {"INQUIRY_RECEIVED", "PAID", "IA_RUNNING", "DRAFT_DONE", "FINAL_UPLOADED", "PUBLISHED"}
    inquiries = (
        ClientInquiry.objects.filter(
            kind=ClientInquiry.KIND_KIT,
            processing_state__in=STATI,
        )
        .prefetch_related("tasks")
        .order_by("-created_at")
    )
    return render(request, "store/kit_complete_processing.html", {"inquiries": inquiries})


@staff_member_required
@require_GET
def kit_complete_inquiry_detail(request, pk: int):
    """
    Detail view for a Kit Complete inquiry.
    Shows client information, text fields, attachments, and current state.
    """
    inquiry = get_object_or_404(
        ClientInquiry.objects.prefetch_related("tasks"),
        pk=pk,
        kind=ClientInquiry.KIND_KIT
    )
    
    # Get attachments
    attachments = InquiryDocument.objects.filter(inquiry=inquiry).order_by("-uploaded_at")
    
    context = {
        "inquiry": inquiry,
        "attachments": attachments,
    }
    
    return render(request, "store/kit_complete_inquiry_detail.html", context)


def _run_kit_ai_generation_sync(inquiry: ClientInquiry) -> None:
    """
    Lance la génération DOCX via la tâche Celery.
    Utilise Celery si disponible; sinon, exécute en synchrone.
    """
    try:
        from .tasks import generate_kit_complete_draft_task
        try:
            # Si Celery est opérationnel
            generate_kit_complete_draft_task.delay(inquiry.pk)
        except Exception:
            # Fallback synchrone
            generate_kit_complete_draft_task(inquiry.pk)
    except Exception as e:
        raise e


@staff_member_required
@require_POST
def kit_complete_process(request, pk: int):
    """
    Process view: triggers AI generation for a Kit Complete inquiry.
    Changes state from PAID to IA_RUNNING and launches Celery task.
    """
    from store.models import KitProcessingTask
    from store.tasks import run_kit_ai_pipeline
    
    inquiry = get_object_or_404(ClientInquiry, pk=pk, kind=ClientInquiry.KIND_KIT)
    
    # Vérifier que la demande est de type KIT
    if inquiry.kind != ClientInquiry.KIND_KIT:
        messages.error(request, "Cette demande n'est pas une demande de Kit complet.")
        return redirect("store:kit_complete_processing")
    
    # Vérifier le paiement
    if inquiry.payment_status != "PAID" and (not inquiry.order or not inquiry.order.is_paid):
        messages.error(request, "Le paiement n'est pas confirmé pour cette demande.")
        return redirect("store:kit_complete_processing")
    
    # Vérifier qu'il n'y a pas déjà une tâche en cours
    active_task = inquiry.tasks.filter(status__in=["PENDING", "RUNNING"]).first()
    if active_task:
        messages.warning(
            request,
            f"Une tâche de traitement est déjà en cours (statut: {active_task.status})."
        )
        return redirect("store:kit_complete_inquiry_detail", pk=pk)
    
    # Vérifier l'état de traitement
    if inquiry.processing_state not in ("INQUIRY_RECEIVED", "PAID"):
        messages.error(request, "Cette demande n'est pas dans un état traitable.")
        return redirect("store:kit_complete_processing")
    
    # Créer une nouvelle KitProcessingTask
    task = KitProcessingTask.objects.create(
        inquiry=inquiry,
        status="PENDING"
    )
    
    # Mettre l'inquiry en IA_RUNNING
    inquiry.processing_state = "IA_RUNNING"
    inquiry.save(update_fields=["processing_state"])
    
    # Lancer la tâche Celery
    try:
        run_kit_ai_pipeline.delay(str(task.id))
        messages.success(
            request,
            "Traitement IA lancé. Le brouillon sera disponible dès qu'il sera prêt."
        )
    except Exception as e:
        error_msg = str(e)
        user_friendly_msg = "Erreur lors du lancement du traitement IA."
        
        # Détecter les erreurs spécifiques
        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            user_friendly_msg = (
                "⚠️ Quota OpenAI dépassé. "
                "Veuillez vérifier votre plan et vos informations de facturation OpenAI. "
                "La tâche a été créée et sera réessayée automatiquement."
            )
        elif "401" in error_msg or "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            user_friendly_msg = (
                "🔑 Clé API OpenAI invalide ou manquante. "
                "Veuillez vérifier la configuration OPENAI_API_KEY."
            )
        elif "timeout" in error_msg.lower():
            user_friendly_msg = (
                "⏱️ Timeout lors de la connexion à l'API OpenAI. "
                "La tâche a été créée et sera réessayée automatiquement."
            )
        else:
            # Pour les autres erreurs, afficher un message générique avec log détaillé
            logger.exception(f"Erreur lors du lancement du traitement IA pour inquiry {pk}: {e}")
            user_friendly_msg = (
                "❌ Erreur lors du lancement du traitement IA. "
                "La tâche a été créée. Veuillez consulter les logs pour plus de détails."
            )
        
        messages.error(request, user_friendly_msg)
        # Ne pas revenir à l'état précédent car la tâche est créée et peut être réessayée
        # inquiry.processing_state = "PAID"
        # inquiry.save(update_fields=["processing_state"])
        task.status = "FAILED"
        task.error = error_msg
        task.save(update_fields=["status", "error"])
    
    return redirect("store:kit_complete_inquiry_detail", pk=pk)


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
    subject = "Votre Kit complet de préparation à l'audit"
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


@staff_member_required
@require_GET
def kit_complete_status(request, pk: int):
    """
    Retourne le statut de traitement IA pour une inquiry donnée (JSON).
    """
    inquiry = get_object_or_404(ClientInquiry, pk=pk, kind=ClientInquiry.KIND_KIT)
    task = inquiry.tasks.order_by("-created_at").first()
    
    payload = {
        "state": inquiry.processing_state,
        "ai_status": inquiry.ai_status,
        "task_status": task.status if task else None,
        "has_draft": hasattr(inquiry, "generated_draft") and inquiry.generated_draft.docx is not None,
    }
    
    # Si un draft existe, ajouter une URL de téléchargement
    if payload["has_draft"] and inquiry.generated_draft.docx:
        payload["draft_url"] = reverse("store:kit_generated_draft_download", args=[inquiry.pk])
    
    return JsonResponse(payload)


@staff_member_required
@require_GET
def kit_generated_draft_download(request, pk: int):
    """
    Vue pour télécharger le brouillon Word généré par l'IA.
    """
    inquiry = get_object_or_404(ClientInquiry, pk=pk, kind=ClientInquiry.KIND_KIT)
    
    if not hasattr(inquiry, "generated_draft") or not inquiry.generated_draft.docx:
        messages.error(request, "Aucun brouillon généré disponible.")
        return redirect("store:kit_complete_inquiry_detail", pk=pk)
    
    draft = inquiry.generated_draft
    file_path = draft.docx.path
    
    response = FileResponse(
        open(file_path, "rb"),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response["Content-Disposition"] = f'attachment; filename="kit_inquiry_{inquiry.pk}.docx"'
    
    return response


