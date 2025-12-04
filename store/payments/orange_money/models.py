"""
Modèles Django pour Orange Money.
"""
import uuid
import logging
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone

logger = logging.getLogger(__name__)


class OrangeMoneyPayment(models.Model):
    """
    Modèle pour tracer les paiements Orange Money.
    """
    STATUS_INITIATED = "initiated"
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_ERROR = "error"
    
    STATUS_CHOICES = [
        (STATUS_INITIATED, "Initiated"),
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_ERROR, "Error"),
    ]
    
    # Référence interne unique
    reference = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Référence interne unique (ex: OM-{uuid})",
    )
    
    # ID transaction Orange Money (peut être null si pas encore créé)
    external_transaction_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID transaction côté Orange Money",
    )
    
    # Statut du paiement
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_INITIATED,
        db_index=True,
    )
    
    # Montant et devise
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Montant en XOF",
    )
    currency = models.CharField(
        max_length=8,
        default="XOF",
    )
    
    # Informations client
    customer_msisdn = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="Numéro téléphone client (MSISDN)",
    )
    
    # Informations marchand
    merchant_id = models.CharField(
        max_length=128,
        blank=True,
        help_text="ID marchand Orange Money",
    )
    
    # Payloads bruts pour traçabilité
    raw_request_payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Payload de la requête API initiale",
    )
    raw_response_payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Réponse de l'API lors de l'initiation",
    )
    callback_payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Payload du webhook/callback Orange Money",
    )
    
    # Relation générique vers Order ou ClientInquiry
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["external_transaction_id"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
        verbose_name = "Paiement Orange Money"
        verbose_name_plural = "Paiements Orange Money"
    
    def __str__(self):
        return f"OrangeMoneyPayment {self.reference} - {self.status} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"OM-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_paid(self) -> bool:
        """Vérifie si le paiement est réussi."""
        return self.status == self.STATUS_SUCCESS
    
    @property
    def is_failed(self) -> bool:
        """Vérifie si le paiement a échoué."""
        return self.status in [self.STATUS_FAILED, self.STATUS_ERROR, self.STATUS_CANCELLED]


class OrangeMoneyPaymentLog(models.Model):
    """
    Logs des événements pour un paiement Orange Money.
    Permet de tracer toutes les interactions sans polluer le modèle principal.
    """
    EVENT_INIT = "init"
    EVENT_CALLBACK = "callback"
    EVENT_RETRY = "retry"
    EVENT_ERROR = "error"
    EVENT_STATUS_CHECK = "status_check"
    
    EVENT_CHOICES = [
        (EVENT_INIT, "Initiation"),
        (EVENT_CALLBACK, "Callback/Webhook"),
        (EVENT_RETRY, "Retry"),
        (EVENT_ERROR, "Error"),
        (EVENT_STATUS_CHECK, "Status Check"),
    ]
    
    payment = models.ForeignKey(
        OrangeMoneyPayment,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    event_type = models.CharField(
        max_length=32,
        choices=EVENT_CHOICES,
        db_index=True,
    )
    payload = models.JSONField(
        default=dict,
        help_text="Payload de l'événement (requête, réponse, erreur, etc.)",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment", "event_type"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Log Paiement Orange Money"
        verbose_name_plural = "Logs Paiements Orange Money"
    
    def __str__(self):
        return f"Log {self.event_type} for {self.payment.reference} at {self.created_at}"

