# DEPLOY.md — LWS cPanel M (Passenger/WSGI)

Déployer un projet Django sous **LWS cPanel M** (hébergement mutualisé) via **Phusion Passenger (WSGI)**.  
Ici, pas de Gunicorn/Nginx à installer : Apache + Passenger s’occupent de servir votre app.

---

## 1) Créer l’application Python (cPanel)

- cPanel → **Setup Python App** → *Create Application* :
  - **Python** : 3.10/3.11
  - **Application root** : `apps/audit-ebooks` (éviter `public_html` pour le code)
  - **Application URL** : choisissez votre domaine ou sous-domaine
  - **Startup file** : `passenger_wsgi.py`
  - **Application entry point** : `application`
- Cliquer **Create**.

> Cette étape crée l’environnement Python et configure Passenger.

---

## 2) Uploader le projet

Placez votre code (le squelette Django) dans **`apps/audit-ebooks/`** (FTP, Git, File Manager).

Arborescence cible (extrait) :
- `apps/audit-ebooks/manage.py`
- `apps/audit-ebooks/config/…`
- `apps/audit-ebooks/core/…`
- `apps/audit-ebooks/store/…`
- `apps/audit-ebooks/templates/…`
- `apps/audit-ebooks/static/`, `apps/audit-ebooks/media/`

---

## 3) Fichier `passenger_wsgi.py`

Dans **`apps/audit-ebooks/passenger_wsgi.py`** :

    # passenger_wsgi.py
    import sys, os
    BASE_DIR = os.path.dirname(__file__)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import config.wsgi
    application = config.wsgi.application

> Si votre paquet de settings ne s’appelle pas `config`, adaptez `DJANGO_SETTINGS_MODULE`.

---

## 4) Variables d’environnement (cPanel)

Dans **Setup Python App**, ajoutez :
- `DJANGO_SETTINGS_MODULE` = `config.settings`
- `DJANGO_SECRET_KEY` = `…`
- `ALLOWED_HOSTS` = `ton-domaine,www.ton-domaine`
- (Paiement) `CINETPAY_API_URL`, `CINETPAY_API_KEY`, `CINETPAY_SITE_ID`, `CINETPAY_RETURN_URL`, `CINETPAY_NOTIFY_URL`

> Alternative : `.env` + `python-dotenv`. Ne **committez pas** `.env`.

---

## 5) Installer les dépendances

Ouvrez **Terminal** dans cPanel (ou SSH), chargez l’environnement de l’app (bouton “Enter to the virtual environment”). Puis :

    pip install -r requirements.txt

Si vous n’avez pas `requirements.txt`, installez manuellement :
- `Django`, `whitenoise`, `pillow`, `requests`, `python-dotenv`, etc.

---

## 6) Migrations & statiques

Toujours dans le Terminal cPanel :

    python manage.py migrate
    python manage.py collectstatic --noinput

> Le squelette utilise **Whitenoise** : vos statiques sont servis par l’app WSGI (pratique sans accès Apache).  
> Option : vous pouvez aussi configurer Apache pour servir `/static/` depuis un dossier mappé, mais Whitenoise suffit en mutualisé.

---

## 7) Tailwind CSS en production (mutualisé)

Deux options :

- **Simple (recommandée au début)** : garder **CDN Tailwind** (déjà dans `base.html`). Pas d’étape build côté serveur.
- **Optimisée** : build **en local** et uploader le CSS minifié :
  1) En local : `npm i -D tailwindcss postcss autoprefixer && npx tailwindcss init -p`
  2) `tailwind.config.js` → `content: ["./templates/**/*.html", "./**/*.py"]`
  3) `static/src/input.css` :
     
         @tailwind base;
         @tailwind components;
         @tailwind utilities;

  4) Build local :
     
         npx tailwindcss -i ./static/src/input.css -o ./static/dist/styles.css --minify

  5) Remplacez le CDN dans `base.html` par :
     
         <link rel="stylesheet" href="{% static 'dist/styles.css' %}">

  6) Uploadez le fichier généré et relancez `collectstatic`.

---

## 8) Redémarrer l’application

Dans **Setup Python App**, cliquez **Restart**.  
Testez l’URL publique. En cas d’erreur 500, vérifiez :
- `passenger_wsgi.py` (chemin, module settings)
- `DJANGO_SETTINGS_MODULE`, `ALLOWED_HOSTS`
- Logs d’erreur Passenger (section “Errors” ou “Application logs”)

---

## 9) CinetPay (retour & webhook)

Dans le **back-office CinetPay** :
- **Return URL** → `https://ton-domaine/payment/return/`
- **Notification URL** (webhook, serveur→serveur) → `https://ton-domaine/payment/callback/`

Ces endpoints sont des vues Django standard : Passenger les reçoit via Apache (WSGI).  
Assurez-vous que votre callback **vérifie le HMAC `x-token`** et appelle **`/v2/payment/check`** avant de livrer le PDF.

---

## 10) Téléchargement sécurisé

Le squelette fournit `/telecharger/<token>/` (FileResponse).  
Le `DownloadToken` expire (ex. 72h). Pour aller plus loin : watermark (email acheteur).

---

## 11) Checklist finale

- [ ] `passenger_wsgi.py` pointe bien vers `config.wsgi`
- [ ] Variables env cPanel OK (`SECRET_KEY`, `ALLOWED_HOSTS`, CinetPay…)
- [ ] `pip install` terminé sans erreur
- [ ] `migrate` OK, `collectstatic` OK
- [ ] (Option) Tailwind local build connecté dans `base.html`
- [ ] CinetPay : Return & Notify en **HTTPS** → OK
- [ ] Webhook : **HMAC** validé + **payment/check** avant livraison
- [ ] Restart app (cPanel) → site OK

---

## 12) Dépannage rapide

- **500 au chargement** : module settings introuvable → corriger `DJANGO_SETTINGS_MODULE` ou `passenger_wsgi.py`.
- **Statiques non chargées** : relancer `collectstatic` ; vérifier Whitenoise est actif dans `MIDDLEWARE` ; vider cache CDN éventuel.
- **Webhook non appelé** : vérifier l’URL publique dans le dashboard CinetPay ; autoriser HTTPS ; inspecter logs Apache/Passenger.
- **Commande bloquée en pending** : implémentez bien `payment/callback/` (HMAC OK) + `payment/check` puis passez en `PAID`.

