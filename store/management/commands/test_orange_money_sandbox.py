"""
Commande Django pour tester l'intégration Orange Money en mode Sandbox.

Usage:
    python manage.py test_orange_money_sandbox
    python manage.py test_orange_money_sandbox --amount 500
    python manage.py test_orange_money_sandbox --check-status ORDER_ID
"""
import json
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from store.models import Order, Product
from store.services import orange_money

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Teste l'intégration Orange Money WebPay Dev (Sandbox). "
        "Crée un paiement de test et affiche la payment_url."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--amount",
            type=int,
            default=100,
            help="Montant de test en FCFA (défaut: 100)",
        )
        parser.add_argument(
            "--check-status",
            type=str,
            help="Vérifier le statut d'une transaction existante (order_id)",
        )
        parser.add_argument(
            "--pay-token",
            type=str,
            help="pay_token pour check-status (optionnel mais recommandé)",
        )

    def handle(self, *args, **options):
        if options.get("check_status"):
            self.check_transaction_status(
                order_id=options["check_status"],
                pay_token=options.get("pay_token"),
            )
            return

        # Créer un paiement de test
        self.create_test_payment(amount=options["amount"])

    def create_test_payment(self, amount: int):
        """Crée un paiement de test et affiche les résultats."""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== Test Orange Money Sandbox (montant: {amount} FCFA) ===\n"
            )
        )

        # Vérifier la configuration
        try:
            from store.services.orange_money import _get_config
            config = _get_config()
            self.stdout.write(
                self.style.SUCCESS("✓ Configuration chargée")
            )
            self.stdout.write(f"  - OAuth URL: {config.get('OAUTH_URL')}")
            self.stdout.write(f"  - WebPay URL: {config.get('WEBPAY_URL')}")
            self.stdout.write(f"  - Merchant Key: {config.get('MERCHANT_KEY', 'N/A')[:10]}...")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur de configuration: {e}")
            )
            return

        # Créer un produit de test si nécessaire
        product = Product.objects.filter(is_published=True).first()
        if not product:
            self.stdout.write(
                self.style.WARNING(
                    "Aucun produit publié trouvé. Création d'un produit de test..."
                )
            )
            product = Product.objects.create(
                slug="test-orange-money",
                title="Test Orange Money",
                price_fcfa=amount,
                is_published=True,
            )

        # Créer un Order de test
        self.stdout.write("\n--- Création de l'Order de test ---")
        order = Order.objects.create(
            product=product,
            amount_fcfa=amount,
            currency="XOF",
            status="PENDING",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone="77011011234",
        )
        self.stdout.write(
            self.style.SUCCESS(f"✓ Order créé: {order.id} (uuid: {order.uuid})")
        )

        # Appeler l'API Orange Money
        self.stdout.write("\n--- Appel API Orange Money WebPay Dev ---")
        try:
            result = orange_money.create_payment_request(order)
            
            payment_url = result.get("payment_url")
            pay_token = result.get("pay_token")
            notif_token = result.get("notif_token")
            order_id = result.get("order_id")
            raw_response = result.get("raw_response", {})

            self.stdout.write(
                self.style.SUCCESS("✓ Paiement créé avec succès\n")
            )
            
            self.stdout.write("=== RÉSULTATS ===\n")
            self.stdout.write(f"Status Code: {raw_response.get('status', 'N/A')}")
            self.stdout.write(f"Message: {raw_response.get('message', 'N/A')}")
            self.stdout.write(f"\nOrder ID: {order_id}")
            self.stdout.write(f"Pay Token: {pay_token[:50] if pay_token else 'N/A'}...")
            self.stdout.write(f"Notif Token: {notif_token[:50] if notif_token else 'N/A'}...")
            self.stdout.write(f"\nPayment URL:\n{self.style.WARNING(payment_url)}\n")
            
            self.stdout.write("\n=== PROCHAINES ÉTAPES ===\n")
            self.stdout.write("1. Copiez la payment_url ci-dessus")
            self.stdout.write("2. Ouvrez-la dans votre navigateur")
            self.stdout.write("3. Connectez-vous au simulateur OTP:")
            self.stdout.write(
                self.style.WARNING(
                    "   https://mpayment.orange-money.com/mpayment-otp/login"
                )
            )
            self.stdout.write("4. Utilisez les identifiants Channel User fournis par Orange")
            self.stdout.write("5. Générez un OTP et validez la transaction")
            self.stdout.write("\n6. Pour vérifier le statut:")
            self.stdout.write(
                self.style.SUCCESS(
                    f"   python manage.py test_orange_money_sandbox "
                    f"--check-status {order_id} --pay-token {pay_token}"
                )
            )
            
            # Mettre à jour l'Order avec les références
            order.provider_ref = order_id
            if pay_token:
                order.cinetpay_payment_id = pay_token
            order.save(update_fields=["provider_ref", "cinetpay_payment_id"])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Order mis à jour avec provider_ref={order_id}"
                )
            )

        except orange_money.OrangeMoneyAuthError as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur d'authentification OAuth: {e}")
            )
        except orange_money.OrangeMoneyAPIError as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur API: {e}")
            )
            if e.response_data:
                self.stdout.write(
                    f"  Détails: {json.dumps(e.response_data, indent=2)}"
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur inattendue: {e}")
            )
            import traceback
            self.stdout.write(traceback.format_exc())

    def check_transaction_status(self, order_id: str, pay_token: str = None):
        """Vérifie le statut d'une transaction."""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== Vérification du statut de la transaction ===\n"
            )
        )
        self.stdout.write(f"Order ID: {order_id}")
        if pay_token:
            self.stdout.write(f"Pay Token: {pay_token[:50]}...")

        # Récupérer l'Order pour obtenir le montant
        order = Order.objects.filter(provider_ref=order_id).first()
        amount = None
        if order:
            amount = int(order.amount_fcfa)
            self.stdout.write(f"Montant: {amount} FCFA")

        try:
            result = orange_money.check_transaction_status(
                order_id=order_id,
                amount=amount,
                pay_token=pay_token,
            )

            status = result.get("status")
            txnid = result.get("txnid")
            raw_response = result.get("raw_response", {})

            self.stdout.write("\n=== RÉSULTAT ===\n")
            self.stdout.write(f"Status: {self.style.SUCCESS(status) if status == 'SUCCESS' else status}")
            if txnid:
                self.stdout.write(f"Transaction ID: {txnid}")
            
            self.stdout.write(f"\nRéponse complète:")
            self.stdout.write(json.dumps(raw_response, indent=2))

            # Interprétation du statut
            self.stdout.write("\n=== INTERPRÉTATION ===\n")
            status_map = {
                "INITIATED": "En attente d'entrée utilisateur",
                "PENDING": "Transaction en cours (utilisateur a cliqué sur Confirmer)",
                "EXPIRED": "Token expiré (utilisateur a cliqué trop tard)",
                "SUCCESS": "Paiement réussi ✓",
                "FAILED": "Paiement échoué ✗",
                "ERROR": "Erreur lors de la vérification",
            }
            interpretation = status_map.get(status, "Statut inconnu")
            self.stdout.write(f"{interpretation}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur lors de la vérification: {e}")
            )
            import traceback
            self.stdout.write(traceback.format_exc())

