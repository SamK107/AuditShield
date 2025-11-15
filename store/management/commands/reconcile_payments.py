"""
Commande de réconciliation des paiements.

Pour PaymentIntent.status=PENDING âgés > 15 min, interroge l'API provider
et corrige le statut (PAID/FAILED).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from store.models import PaymentIntent

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Réconcilie les paiements en attente avec les providers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les paiements à réconcilier sans les modifier",
        )
        parser.add_argument(
            "--min-age",
            type=int,
            default=15,
            help="Âge minimum en minutes pour réconcilier (défaut: 15)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        min_age_minutes = options["min_age"]
        
        cutoff_time = timezone.now() - timedelta(minutes=min_age_minutes)
        
        pending_intents = PaymentIntent.objects.filter(
            status="PENDING",
            created_at__lt=cutoff_time,
        ).select_related("inquiry", "inquiry__order")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Trouvé {pending_intents.count()} paiements en attente "
                f"depuis plus de {min_age_minutes} minutes"
            )
        )
        
        reconciled = 0
        errors = 0
        
        for intent in pending_intents:
            try:
                self.stdout.write(
                    f"\nRéconciliation PaymentIntent #{intent.id} "
                    f"(provider={intent.provider}, external_ref={intent.external_ref})"
                )
                
                if not intent.external_ref:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ external_ref manquant, skip"
                        )
                    )
                    continue
                
                # Vérifier selon le provider
                if intent.provider == "cinetpay":
                    from store.services.cinetpay import payment_check
                    
                    is_paid, provider_tx_id = payment_check(intent.external_ref)
                    
                    if dry_run:
                        self.stdout.write(
                            f"  [DRY-RUN] Statut: {'PAID' if is_paid else 'FAILED'}"
                        )
                    else:
                        if is_paid:
                            intent.status = "PAID"
                            intent.inquiry.payment_status = "PAID"
                            intent.inquiry.processing_state = "PAID"
                            if intent.inquiry.order:
                                intent.inquiry.order.status = "PAID"
                                intent.inquiry.order.paid_at = timezone.now()
                                intent.inquiry.order.save(update_fields=["status", "paid_at"])
                            
                            # Enqueue Celery si pas déjà fait
                            from store.tasks import build_kit_word
                            try:
                                build_kit_word.delay(intent.inquiry.id)
                                self.stdout.write(
                                    self.style.SUCCESS("  ✓ Tâche Celery enqueued")
                                )
                            except Exception as e:
                                logger.exception(f"Erreur enqueue Celery: {e}")
                            
                            self.stdout.write(
                                self.style.SUCCESS("  ✓ Paiement confirmé")
                        else:
                            intent.status = "FAILED"
                            intent.inquiry.payment_status = "FAILED"
                            self.stdout.write(
                                self.style.ERROR("  ✗ Paiement échoué")
                            )
                        
                        intent.save(update_fields=["status"])
                        intent.inquiry.save(update_fields=["payment_status", "processing_state"])
                        
                        reconciled += 1
                
                elif intent.provider == "om":
                    from store.services.orange_money import check_transaction_status
                    
                    is_paid, provider_tx_id = check_transaction_status(intent.external_ref)
                    
                    if dry_run:
                        self.stdout.write(
                            f"  [DRY-RUN] Statut: {'PAID' if is_paid else 'FAILED'}"
                        )
                    else:
                        if is_paid:
                            intent.status = "PAID"
                            intent.inquiry.payment_status = "PAID"
                            intent.inquiry.processing_state = "PAID"
                            if intent.inquiry.order:
                                intent.inquiry.order.status = "PAID"
                                intent.inquiry.order.paid_at = timezone.now()
                                intent.inquiry.order.save(update_fields=["status", "paid_at"])
                            
                            from store.tasks import build_kit_word
                            try:
                                build_kit_word.delay(intent.inquiry.id)
                                self.stdout.write(
                                    self.style.SUCCESS("  ✓ Tâche Celery enqueued")
                                )
                            except Exception as e:
                                logger.exception(f"Erreur enqueue Celery: {e}")
                            
                            self.stdout.write(
                                self.style.SUCCESS("  ✓ Paiement confirmé")
                        else:
                            intent.status = "FAILED"
                            intent.inquiry.payment_status = "FAILED"
                            self.stdout.write(
                                self.style.ERROR("  ✗ Paiement échoué")
                            )
                        
                        intent.save(update_fields=["status"])
                        intent.inquiry.save(update_fields=["payment_status", "processing_state"])
                        
                        reconciled += 1
                
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Provider inconnu: {intent.provider}")
                    )
            
            except Exception as e:
                errors += 1
                logger.exception(f"Erreur réconciliation PaymentIntent #{intent.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Erreur: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Réconciliation terminée: {reconciled} réconciliés, {errors} erreurs"
            )
        )

