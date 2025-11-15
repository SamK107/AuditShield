import email
import imaplib
import re
from datetime import datetime, timezone
from email.header import decode_header, make_header
from typing import Optional

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.conf import settings

from downloads.models import ExternalEntitlement, DownloadCategory
from store.services.mailing import send_fulfilment_email


ORDER_RE = re.compile(r"(EXT|REF|ORD|CP|TX)[-_ ]?([A-Z0-9]{4,})", re.I)


def _decode(s):
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


def _guess_platform(from_addr: str) -> str:
    f = (from_addr or "").lower()
    if "youscribe" in f:
        return "youscribe"
    if "publiseer" in f:
        return "publiseer"
    if "chariow" in f:
        return "chariow"
    return "other"


def _find_first_category() -> Optional[DownloadCategory]:
    try:
        return DownloadCategory.objects.all().order_by("order", "slug").first()
    except Exception:
        return None


class Command(BaseCommand):
    help = "Récupère les reçus d’achat via IMAP et crée des ExternalEntitlement (idempotent via Message-ID)."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Traiter tous les emails (et pas seulement UNSEEN)")
        parser.add_argument("--dry-run", action="store_true", help="Ne pas écrire en BD ni envoyer d’emails")
        parser.add_argument("--folder", type=str, help="Dossier IMAP à lire (override)")

    def handle(self, *args, **opts):
        host = getattr(settings, "RECEIPTS_IMAP_HOST", None) or "imap.auditsanspeur.com"
        port = int(getattr(settings, "RECEIPTS_IMAP_PORT", None) or 993)
        user = getattr(settings, "RECEIPTS_IMAP_USER", None)
        pwd = getattr(settings, "RECEIPTS_IMAP_PASSWORD", None)
        folder = opts.get("folder") or getattr(settings, "RECEIPTS_IMAP_FOLDER", None) or "INBOX"
        process_all = bool(opts.get("all"))
        dry_run = bool(opts.get("dry_run"))

        if not user or not pwd:
            self.stderr.write(self.style.ERROR("IMAP creds missing (RECEIPTS_IMAP_USER / RECEIPTS_IMAP_PASSWORD)"))
            return

        self.stdout.write(self.style.NOTICE(f"Connecting IMAP {host}:{port} folder={folder} all={process_all} dry={dry_run}"))
        M = imaplib.IMAP4_SSL(host, port)
        try:
            M.login(user, pwd)
            M.select(folder)
            criteria = "ALL" if process_all else "UNSEEN"
            typ, data = M.search(None, criteria)
            if typ != "OK":
                self.stderr.write(self.style.ERROR(f"IMAP search error: {typ} {data!r}"))
                return
            ids = data[0].split()
            self.stdout.write(f"Found {len(ids)} message(s)")
            processed = 0
            for num in ids:
                typ, msg_data = M.fetch(num, "(RFC822)")
                if typ != "OK":
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                message_id = (msg.get("Message-ID") or "").strip()
                from_addr = _decode(msg.get("From"))
                subject = _decode(msg.get("Subject"))

                # Idempotence
                if message_id and ExternalEntitlement.objects.filter(message_id=message_id).exists():
                    self.stdout.write(self.style.WARNING(f"Skip already processed: {message_id}"))
                    continue

                # Parse order ref
                order_ref = None
                m = ORDER_RE.search(subject or "")
                if m:
                    order_ref = f"{m.group(1).upper()}-{m.group(2).upper()}"
                # Body fallback
                if not order_ref:
                    body_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            ctype = part.get_content_type()
                            if ctype == "text/plain":
                                try:
                                    body_text = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                                except Exception:
                                    body_text = ""
                                break
                    else:
                        try:
                            body_text = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
                        except Exception:
                            body_text = ""
                    m2 = ORDER_RE.search(body_text or "")
                    if m2:
                        order_ref = f"{m2.group(1).upper()}-{m2.group(2).upper()}"

                # Email dest
                email_match = re.search(r"<([^>]+@[^>]+)>", from_addr) or re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", from_addr, re.I)
                buyer_email = (email_match.group(1) if email_match else from_addr or "").strip()

                platform = _guess_platform(from_addr)
                cat = _find_first_category()
                if not cat:
                    self.stderr.write(self.style.ERROR("No DownloadCategory found; aborting"))
                    return

                if dry_run:
                    self.stdout.write(f"[DRY] Would create entitlement: {buyer_email} -> {cat.slug} ({platform}) order_ref={order_ref}")
                else:
                    obj, created = ExternalEntitlement.objects.get_or_create(
                        email=buyer_email,
                        category=cat,
                        platform=platform,
                        order_ref=order_ref,
                        defaults={
                            "message_id": message_id or None,
                            "raw_payload": f"FROM: {from_addr}\nSUBJECT: {subject}",
                            "processed_at": now(),
                        },
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created entitlement for {buyer_email} [{platform}]"))
                        # Email fulfilment
                        try:
                            send_fulfilment_email(to_email=buyer_email, order_ref=order_ref)
                        except Exception as e:
                            self.stderr.write(self.style.WARNING(f"Mail send failed: {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Entitlement already exists for {buyer_email} ({platform}/{cat.slug})"))

                # Mark seen and move to Processed
                try:
                    if not dry_run:
                        M.store(num, "+FLAGS", "\\Seen")
                        try:
                            M.copy(num, "Processed")
                            M.store(num, "+FLAGS", "\\Deleted")
                        except Exception:
                            pass
                except Exception:
                    pass
                processed += 1

            self.stdout.write(self.style.SUCCESS(f"Done. Processed {processed} messages"))
        finally:
            try:
                M.expunge()
                M.logout()
            except Exception:
                pass

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