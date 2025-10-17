# Site Ebook – Django + HTMX + Tailwind + Alpine + Lucide (CinetPay)

## But
V1 simple “à la Acquisition.com” : page produit persuasive (promesse, preuves sociales, FAQ, garantie), 3 offres (Standard / Personnalisation / Formation), exemples d’irrégularités (carrousel), paiement CinetPay, téléchargement sécurisé.

## Principes & Stack
- **Stack** : Django 5 • HTMX • Alpine.js • Tailwind CSS • Icônes Lucide.
- **Design** : minimal, pro, mobile-first, CTA visibles, sections courtes qui convertissent.
- **Perf** : pages légères, Tailwind purgé en prod, images comprimées.
- **Sécurité** : lien de téléchargement sécurisé (token + expiration), webhook signature HMAC (à brancher).

---

## Quickstart (dev)

    python -m venv .venv
    # macOS/Linux
    source .venv/bin/activate
    # Windows PowerShell
    # .venv\Scripts\Activate.ps1

    OK ==> pip install "Django>=5.0" whitenoise pillow requests python-dotenv 

    # Crée le projet dans le dossier courant (le point ".")
    django-admin startproject config .

    # Apps
    python manage.py startapp core
    python manage.py startapp store

    # → Coller/ajouter les fichiers du squelette (settings/urls/models/templates/services/seed)
    python manage.py migrate

    # (Option) Crée un superuser
    # macOS/Linux
    # export DJANGO_SUPERUSER_USERNAME=admin
    # export DJANGO_SUPERUSER_EMAIL=admin@example.com
    # export DJANGO_SUPERUSER_PASSWORD=admin12345
    # python manage.py createsuperuser --noinput
    #
    # Windows PowerShell
    # $env:DJANGO_SUPERUSER_USERNAME="admin"
    # $env:DJANGO_SUPERUSER_EMAIL="admin@example.com"
    # $env:DJANGO_SUPERUSER_PASSWORD="admin12345"
    # python manage.py createsuperuser --noinput

    # Données d’exemple (produit, offres, exemples, médias)
    python manage.py seed_store

    # Run
    python manage.py runserver

Visite : `/`, `/ebook/audit-sans-peur/`, `/offres/`, `/exemples/`.

---

## Arborescence visée

    ./                     # repo racine
      manage.py
      config/
        settings.py, urls.py, wsgi.py, asgi.py
      core/
        urls.py, views.py
        templates/core/ (home, about, policy, cgv, contact)
      store/
        models.py, urls.py, views.py, admin.py
        services/cinetpay.py          # MOCK → à brancher CinetPay réel
        management/commands/seed_store.py
        templates/store/
          base.html
          product_detail.html         # page produit persuasive
          offers.html                 # 3 offres (cartes)
          examples.html               # carrousel irrégularités
          thank_you.html              # page merci + download
      static/
      media/

---

## Pages & Routes

- **Accueil** `/` — promesse claire, CTA “Voir le livre” / “Voir les offres”, aperçu d’exemples.
- **Produit** `/ebook/<slug>/` — promesse, ce que vous obtenez, media/extraits (PDF + vidéo), preuves sociales, FAQ, garantie, CTA sticky mobile.
- **Offres** `/offres/` — 3 cartes : Standard (15 000 FCFA – BUY), Personnalisation (QUOTE), Formation & Assistance (CALL).
- **Exemples** `/exemples/` — carrousel “Irrégularités & Traitements” (HTMX + Alpine).
- **Paiement** :  
  - `POST /buy/<slug>/` → crée Order(pending) + init paiement (mock)  
  - `/payment/return/` → page retour utilisateur (merci / échec)  
  - `/payment/callback/` (POST) → webhook CinetPay (à sécuriser HMAC)
- **Téléchargement** `/telecharger/<token>/` — FileResponse sécurisé (token 72h).
- **Confiance** `/a-propos/`, `/politique/`, `/cgv/`, `/contact/`.

---

## Modèles (MVP)

- **Product**(slug, title, subtitle, price_fcfa, hero_image?, guarantee_text, faq_json[], social_proofs_json[], deliverable_file?, is_published)
- **OfferTier**(product, kind=[STANDARD|PERSONNALISATION|FORMATION], price_fcfa?, description_md, cta_type=[BUY|QUOTE|CALL])
- **ExampleSlide**(product, title, irregularity, indicators?, legal_ref?, remedy, risks?, sample_doc_url?, image?)
- **MediaAsset**(product, kind=[PDF_EXTRACT|VIDEO], title, file_or_url, thumb?)
- **Order**(order_id UUID, product, email, amount_fcfa, status=[pending|paid|failed], cinetpay_payment_id?, created_at)
- **DownloadToken**(order 1–1, token UUID, expires_at, is_valid())

> **Standard (15 000 FCFA)** inclut : ebook “Ebook - Audit Sans Peur” + **bonus** “Dossier irrégularités & solutions (1 texte au choix)” + “Guide de l’audit en 7 étapes”.

---

## Composants UI (réutilisables)

- **FAQ accordéon** (Alpine) — objections courantes (format, MAJ, remboursement, support, usage pro…)
- **Carrousel irrégularités** (Alpine) — 2–5 slides : irrégularité → indicateurs → référence → traitement → risques → pièce modèle.
- **Bandeau CTA sticky (mobile)** — prix + bouton “Obtenir l’ebook”.

Palette suggérée : **Bleu pro** (#1D4ED8), gris neutres (#111827, #6B7280, #F3F4F6).  
Typo : Inter (texte), Source Serif 4 (titres optionnel).  
Icônes : Lucide (`check`, `shield`, `lock`, `credit-card`, `book-open`, `file-text`).

---

## Flux CinetPay (à brancher en prod)

1. **Init paiement** : `POST /buy/<slug>/` → créer `Order(pending)` (email, montant, produit) → appeler `services/cinetpay.init_payment(order)` → rediriger vers **URL CinetPay**.
2. **Webhook** `POST /payment/callback/` (serveur↔serveur) : vérifier **signature HMAC** (secret CinetPay), récupérer l’état, passer `Order.status='paid'`, créer `DownloadToken` (exp. 72h).
3. **Retour navigateur** `/payment/return/` : afficher Merci + lien Télécharger si déjà payé (sinon indiquer “en attente de confirmation”).
4. **Téléchargement** `/telecharger/<token>/` : streaming sécurisé, invalide si expiré.

**À faire** : implémenter les vrais appels API CinetPay + contrôle de signature HMAC dans `services/cinetpay.py`. Stocker les secrets en `.env`.

---

## .env (exemple)

    DJANGO_DEBUG=1
    DJANGO_SECRET_KEY=change-me
    ALLOWED_HOSTS=localhost,127.0.0.1

    CINETPAY_API_KEY=...
    CINETPAY_SECRET=...
    CINETPAY_SITE_ID=...
    CINETPAY_RETURN_URL=http://127.0.0.1:8000/payment/return/
    CINETPAY_NOTIFY_URL=http://127.0.0.1:8000/payment/callback/

> **Ne jamais** committer `.env`. Ajouter au `.gitignore`.

---

## Règles Cursor (pinned / rappel)

- Pas de frameworks lourds : **HTMX + Alpine + Tailwind** suffisent.
- Respecter l’**arborescence** & les **routes** ci-dessus.
- Réutiliser les **composants** (FAQ, carrousel, CTA sticky).
- Icônes **Lucide** via `data-lucide` (+ `lucide.createIcons()` au load).
- Pas de secrets en clair ; utiliser `python-dotenv`.
- Code clair, testable : logique paiement isolée dans `services/cinetpay.py`.

---

## Déploiement (mémo)

- `DEBUG=False`, `ALLOWED_HOSTS` (domaine), `SECRET_KEY` fort.
- **Whitenoise** activé (statiques).  
- **Tailwind** : en prod, remplacer CDN par build CLI purgé :
  1) `npm i -D tailwindcss postcss autoprefixer && npx tailwindcss init -p`
  2) `content` → scanner `templates/**/*.html`
  3) `static/src/input.css` :
     
         @tailwind base;
         @tailwind components;
         @tailwind utilities;

  4) Build :
     
         npx tailwindcss -i ./static/src/input.css -o ./static/dist/styles.css --minify

  5) Lier dans `base.html` :  
     
         <link rel="stylesheet" href="{% static 'dist/styles.css' %}">

  6) `python manage.py collectstatic`

- Base de données : SQLite (dev) → Postgres (prod) recommandé.
- SSL/TLS (reverse proxy), redirections www/non-www, GZIP/Brotli.

---

## Roadmap (facultatif)

- Watermark email acheteur sur PDF délivré.  
- Coupons / bundles / multi-produits.  
- Emails transactionnels (payé, lien de téléchargement, MAJ).  
- Formulaire **“Demander un devis”** (Personnalisation/Formation) + CRM léger.  
- Tests unitaires (services paiement, webhook, download).  
- SEO (OpenGraph, titres uniques), sitemap, robots.

---

## Licence & mentions (à adapter)

- © [Ton nom / Ta société], [année].  
- Paiement sécurisé par **CinetPay**. Garantie **7 jours**.  
- Références juridiques : textes nationaux, UEMOA, bailleurs — vérifier l’actualité avant toute décision.

