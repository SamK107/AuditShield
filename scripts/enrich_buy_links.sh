#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Active le venv si besoin
if [ -z "${VIRTUAL_ENV:-}" ]; then
  source ~/virtualenv/apps/auditshield/3.12/bin/activate
fi

echo "[*] Using venv: ${VIRTUAL_ENV:-<none>}"
echo "[*] Project root: $PWD"

# 1) Backup
cp -a config/settings.py "config/settings.py.bak.$(date +%F-%H%M%S)"
echo "[*] Backup done."

# 2) Détecter le slug standard via manage.py (Django auto-configuré)
STD_SLUG="$(
  ./manage.py shell -c '
from store.models import Product
p = getattr(Product.objects, "filter", Product.objects)(is_standard=True).first() or Product.objects.order_by("id").first()
print(p.slug if p else "", end="")
' 2>/dev/null
)"

if [ -z "$STD_SLUG" ]; then
  echo "[!] Impossible de déduire le slug. Faites : export STD_SLUG=mon-produit && bash scripts/enrich_buy_links.sh"
  exit 1
fi
echo "[*] Detected STD_SLUG=${STD_SLUG}"

# 3) Injecter/merger EXTERNAL_BUY_LINKS (append safe)
cat >> config/settings.py <<'PYSET'
# --- BEGIN AUTOGEN: EXTERNAL_BUY_LINKS enrichment ---
EXTERNAL_BUY_LINKS = globals().get("EXTERNAL_BUY_LINKS", {})

EXTERNAL_BUY_LINKS.setdefault("__STD_SLUG__", {}).update({
    "selar": {
        "label": "Selar",
        "url": "https://selar.co/ta-page-produit",
        "badge": "Recommandé",
        "description": "Paiement Mobile Money/CB — adapté Afrique de l’Ouest.",
        "help": "<p>Astuce : utilisez un numéro Mobile Money actif (Orange/MTN/Moov).</p>",
        "faq": "<ul><li><strong>Je reçois quoi ?</strong> L’ebook PDF. Les liens dans l’ebook ouvrent les bonus sécurisés sur auditsanspeur.com.</li><li><strong>Paiement en attente ?</strong> Réessayez ou contactez le support.</li></ul>",
    },
    "publiseer": {
        "label": "Publiseer",
        "url": "https://publiseer.com/ta-page-produit",
        "description": "Distribution mondiale (Amazon, Google Play Books, Apple Books).",
        "help": "<p>Idéal pour acheter via les stores internationaux.</p>",
        "faq": "<ul><li><strong>Compatibilité :</strong> lecture via apps iOS/Android/Kindle.</li></ul>",
    },
    "youscribe": {
        "label": "YouScribe Afrique",
        "url": "https://youscribe.com/ta-page-produit",
        "description": "Portée francophone, abonnement/achat local.",
        "help": "<p>Connectez-vous à votre compte YouScribe puis achetez depuis votre pays.</p>",
        "faq": "<ul><li><strong>Accès bonus :</strong> via les liens sécurisés dans l’ebook.</li></ul>",
    },
    "chariow": {
        "label": "Chariow",
        "url": "https://chariow.com/ta-page-produit",
        "description": "Extension régionale et moyens de paiement locaux.",
        "help": "<p>Choisissez la devise locale si disponible.</p>",
        "faq": "<ul><li><strong>Facturation :</strong> reçu fourni par la plateforme.</li></ul>",
    },
})
# --- END AUTOGEN: EXTERNAL_BUY_LINKS enrichment ---
PYSET

# Remplacer le placeholder par le vrai slug
esc_slug="$(printf '%s' "$STD_SLUG" | sed 's/[\/&]/\\&/g')"
sed -i "s/__STD_SLUG__/$esc_slug/g" config/settings.py
echo "[*] settings.py updated."

# 4) Vérifier via manage.py
./manage.py shell -c "
from django.conf import settings; from pprint import pprint
pprint(settings.EXTERNAL_BUY_LINKS.get('${STD_SLUG}'))
"

# 5) Commit/push + restart
git add config/settings.py
git commit -m "settings: enrich EXTERNAL_BUY_LINKS (Selar/Publiseer/YouScribe/Chariow) with description/help/faq"
git push
touch tmp/restart.txt
echo "[*] Done. Check: /buy/${STD_SLUG}/autres/"
