"""
Commande Django pour simuler un paiement Orange Money réussi (sandbox).
Permet de tester le pipeline complet sans appeler l'API Orange Money.

Usage:
    python manage.py simulate_orange_payment_success <reference>
    python manage.py simulate_orange_payment_success --order-id <order_id>
    python manage.py simulate_orange_payment_success --inquiry-id <inquiry_id>
"""
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from store.models import Order, ClientInquiry
from store.payments.orange_money.models import OrangeMoneyPayment, OrangeMoneyPaymentLog
from store.payments.orange_money.views import orange_payment_notify

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simule un paiement Orange Money réussi pour tester le pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "reference",
            nargs="?",
            type=str,
            help="Référence du paiement Orange Money (ex: OM-ABC123)",
        )
        parser.add_argument(
            "--order-id",
            type=int,
            help="ID de l'Order à simuler",
        )
        parser.add_argument(
            "--inquiry-id",
            type=int,
            help="ID du ClientInquiry (Kit complet) à simuler",
        )

    def handle(self, *args, **options):
        reference = options.get("reference")
        order_id = options.get("order_id")
        inquiry_id = options.get("inquiry_id")
        
        # Déterminer l'objet métier
        order_obj = None
        om_payment = None
        
        if order_id:
            order_obj = Order.objects.filter(pk=order_id).first()
            if not order_obj:
                raise CommandError(f"Order {order_id} introuvable")
        elif inquiry_id:
            inquiry = ClientInquiry.objects.filter(pk=inquiry_id).first()
            if not inquiry:
                raise CommandError(f"ClientInquiry {inquiry_id} introuvable")
            order_obj = inquiry.order
            if not order_obj:
                raise CommandError(f"Aucune commande associée à l'inquiry {inquiry_id}")
        elif reference:
            # Chercher le paiement par référence
            om_payment = OrangeMoneyPayment.objects.filter(reference=reference).first()
            if not om_payment:
                raise CommandError(f"Paiement Orange Money avec référence {reference} introuvable")
            order_obj = om_payment.content_object
        else:
            raise CommandError(
                "Fournissez soit une référence, soit --order-id, soit --inquiry-id"
            )
        
        if not order_obj:
            raise CommandError("Aucune commande trouvée")
        
        # Créer ou récupérer le paiement Orange Money
        if not om_payment:
            om_payment, created = OrangeMoneyPayment.objects.get_or_create(
                reference=f"OM-{order_obj.provider_ref or order_obj.uuid}",
                defaults={
                    "status": OrangeMoneyPayment.STATUS_INITIATED,
                    "amount": int(order_obj.amount_fcfa),
                    "currency": order_obj.currency or "XOF",
                    "customer_msisdn": getattr(order_obj, "phone", None) or "77011011234",
                    "merchant_id": "",
                }
            )
            # Lier l'objet métier
            om_payment.content_object = order_obj
            om_payment.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Simulation du paiement pour {om_payment.reference} "
                f"(Order #{order_obj.id})"
            )
        )
        
        # Construire un payload de callback simulé
        simulated_payload = {
            "reference": om_payment.reference,
            "transaction_id": om_payment.external_transaction_id or f"OM-TX-{om_payment.reference}",
            "status": "SUCCESS",
            "amount": str(int(om_payment.amount)),
            "currency": om_payment.currency,
            "customer_msisdn": om_payment.customer_msisdn,
            "timestamp": str(om_payment.created_at),
        }
        
        self.stdout.write(
            f"Payload simulé: {json.dumps(simulated_payload, indent=2)}"
        )
        
        # Créer une requête mock pour appeler la vue notify
        from django.test import RequestFactory
        from django.http import JsonResponse
        
        factory = RequestFactory()
        request = factory.post(
            "/payments/orange/notify/",
            data=json.dumps(simulated_payload),
            content_type="application/json",
        )
        
        # Appeler la vue notify
        try:
            response = orange_payment_notify(request)
            self.stdout.write(
                self.style.SUCCESS(f"Réponse de notify: {response.status_code}")
            )
            
            # Vérifier que le paiement a été mis à jour
            om_payment.refresh_from_db()
            if om_payment.status == OrangeMoneyPayment.STATUS_SUCCESS:
                self.stdout.write(
                    self.style.SUCCESS("✓ Paiement marqué comme SUCCESS")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Statut du paiement: {om_payment.status} (attendu: SUCCESS)"
                    )
                )
            
            # Vérifier que la commande est payée
            order_obj.refresh_from_db()
            if order_obj.status == "PAID":
                self.stdout.write(
                    self.style.SUCCESS("✓ Commande marquée comme PAYEE")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Statut de la commande: {order_obj.status} (attendu: PAID)"
                    )
                )
            
            # Afficher les logs créés
            logs_count = om_payment.logs.count()
            self.stdout.write(
                self.style.SUCCESS(f"✓ {logs_count} log(s) créé(s)")
            )
            
        except Exception as e:
            logger.exception("Erreur lors de la simulation")
            raise CommandError(f"Erreur lors de la simulation: {e}")
        
        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Simulation terminée avec succès !\n"
                f"Vous pouvez maintenant vérifier:\n"
                f"- Order #{order_obj.id}: {order_obj.status}\n"
                f"- OrangeMoneyPayment {om_payment.reference}: {om_payment.status}\n"
                f"- Logs: {om_payment.logs.count()} événement(s)"
            )
        )

