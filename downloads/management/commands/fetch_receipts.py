import email
import imaplib
from email.header import decode_header, make_header
import re
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from downloads.models import ExternalEntitlement
def _get_default_category():
    # Résout le modèle cible du FK 'category' depuis ExternalEntitlement
    CategoryModel = ExternalEntitlement._meta.get_field('category').remote_field.model
    # Prend une catégorie existante si possible (utilise 'order' au lieu de 'id')
    cat = CategoryModel.objects.order_by('order').first()
    if cat:
        return cat
    # Aucune catégorie en base : on ne devine pas les champs requis -> on explique quoi faire
    from django.core.management.base import CommandError
    raise CommandError("Aucune categorie disponible pour renseigner 'category_id' (NOT NULL). Creer une categorie via l'admin (ex: 'Bonus kit'), puis relancer.")

ORDER_REF_REGEX = re.compile(r"\b((?:EXT|REF|REFERENCE|COMMANDE|ORDER)[\s:#-]*[A-Z0-9]+(?:-[A-Z0-9]+)*)\b", re.I)
def _decode_subject(raw_subj):
    if not raw_subj:
        return ""
    try:
        return str(make_header(decode_header(raw_subj)))
    except Exception:
        return raw_subj or ""



class Command(BaseCommand):
    help = "Ingestion IMAP des emails d'achat (receipts@) -> ExternalEntitlement"

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Traiter tous les emails (pas seulement UNSEEN)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limiter le nombre de messages à traiter (0 = illimité)',
        )

    def handle(self, *args, **opts):
        import os
        host = getattr(settings, 'RECEIPTS_IMAP_HOST', None) or os.environ.get('RECEIPTS_IMAP_HOST') or 'imap.auditsanspeur.com'
        port = int(getattr(settings, "RECEIPTS_IMAP_PORT", 993))
        user = getattr(settings, 'RECEIPTS_IMAP_USER', None) or os.environ.get('RECEIPTS_IMAP_USER')
        pwd = getattr(settings, 'RECEIPTS_IMAP_PASSWORD', None) or os.environ.get('RECEIPTS_IMAP_PASSWORD')
        folder = getattr(settings, 'RECEIPTS_IMAP_FOLDER', None) or os.environ.get('RECEIPTS_IMAP_FOLDER', 'INBOX')

        if not all([host, user, pwd]):
            raise CommandError("IMAP non configuré (vars manquantes)")

        M = imaplib.IMAP4_SSL(host, port)
        M.login(user, pwd)
        M.select(folder)

        # --- Recherche des messages (UID) + assainissement des IDs ---
        # On travaille en UID pour éviter les erreurs dues aux numéros de séquence volatils.
        if opts.get('all'):
            typ, data = M.uid('search', None, 'ALL')
        else:
            typ, data = M.uid('search', None, 'UNSEEN')
        
        if typ != "OK" or not data:
            self.stdout.write("Aucun message à traiter pour ce critère.")
            M.close()
            M.logout()
            return

        raw = data[0] or b""
        # Garder uniquement des tokens bytes contenant des chiffres (ex: b'12345')
        uid_rx = re.compile(rb"^\d+$")
        uids = [tok for tok in raw.split() if tok and uid_rx.match(tok)]
        count = len(uids)
        self.stdout.write(f"IDs trouvés: {count}")
        
        if count == 0:
            self.stdout.write("Boîte vide pour ce critère (ALL/UNSEEN). Rien à traiter.")
            M.close()
            M.logout()
            return

        limit = opts.get('limit', 0)
        processed = 0
        for i, uid in enumerate(uids, 1):
            if limit and i > limit:
                self.stdout.write(f"Limite de {limit} atteinte. Arrêt du traitement.")
                break
            
            self.stdout.write(f"[{i}/{count}] Traitement UID {uid.decode('utf-8')}")
            
            # Récupération du message complet par UID
            try:
                typ, msg_data = M.uid('fetch', uid, '(RFC822)')
            except Exception as e:
                self.stderr.write(f"⚠️  FETCH UID échoué pour {uid!r}: {e}")
                continue
            
            if typ != "OK" or not msg_data or not msg_data[0]:
                self.stderr.write(f"⚠️  FETCH UID non OK pour {uid!r}")
                continue

            try:
                msg = email.message_from_bytes(msg_data[0][1])
            except Exception as e:
                self.stderr.write(f"⚠️  Erreur de parsing pour {uid!r}: {e}")
                continue
            decoded_subj = _decode_subject(msg.get('Subject'))
            self.stdout.write(f"  Subject: {decoded_subj}")
            
            from_addr = email.utils.parseaddr(msg.get("From", ""))[1].lower()
            
            # Ignorer les emails système
            if any(x in from_addr for x in ('cpanel', 'dovecotfw', 'webmail', 'mailer-daemon', 'postmaster')):
                self.stdout.write(f"  ↷ Système ignoré: {from_addr}")
                # Marquer comme vu pour ne pas le retraiter
                if not opts.get('all'):
                    try:
                        M.uid('store', uid, '+FLAGS', '(\\Seen)')
                    except Exception as e:
                        self.stderr.write(f"  ⚠️  STORE/Seen échoué pour {uid!r}: {e}")
                continue

            candidates = []
            if msg.get("Subject"):
                candidates += ORDER_REF_REGEX.findall(decoded_subj)
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text += payload.decode(errors="ignore") + "\n"
            else:
                if msg.get_content_type() == "text/plain":
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body_text += payload.decode(errors="ignore")
            candidates += ORDER_REF_REGEX.findall(body_text)

            if not candidates:
                self.stdout.write(f"  ⚠️  Pas de ref trouvée pour email de {from_addr}")
                # Marquer comme vu si on ne traite que les UNSEEN
                if not opts.get('all'):
                    try:
                        M.uid('store', uid, '+FLAGS', '(\\Seen)')
                    except Exception as e:
                        self.stderr.write(f"  ⚠️  STORE/Seen échoué pour {uid!r}: {e}")
                continue

            order_ref = candidates[0].upper()
            # resolve default category (NOT NULL)
            cat = _get_default_category()
            
            ent, created = ExternalEntitlement.objects.get_or_create(
                order_ref=order_ref,
                defaults={
                    "email": from_addr,
                    "platform": "external",
                    "category": cat,
                }
            )
            if not created and ent.email != from_addr:
                ent.email = from_addr
                ent.save(update_fields=["email"])

            self.stdout.write(f"  ✔️  Entitlement {'créé' if created else 'mis à jour'}: {order_ref} <{from_addr}>")
            processed += 1

            # Marquer comme vu si on ne traite que les UNSEEN
            if not opts.get('all'):
                try:
                    M.uid('store', uid, '+FLAGS', '(\\Seen)')
                except Exception as e:
                    self.stderr.write(f"  ⚠️  STORE/Seen échoué pour {uid!r}: {e}")

            # Déplacer le mail traité dans le dossier "Processed" et le marquer pour suppression
            try:
                M.uid('copy', uid, "Processed")
                M.uid('store', uid, '+FLAGS', '(\\Deleted)')
            except Exception as e:
                self.stderr.write(f"  ⚠️  Erreur de déplacement pour {uid!r}: {e}")

        # Purger ce qui est marqué supprimé (une seule fois à la fin)
        try:
            M.expunge()
        except Exception as e:
            self.stderr.write(f"⚠️  Expunge error: {e}")

        self.stdout.write(f"\n✅ Traitement terminé: {processed} entitlement(s) traité(s)")


        M.close()
        M.logout()