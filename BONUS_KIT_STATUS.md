# État des Lieux - Traitement Bonus Kit de Préparation

## 📍 URL de départ
**Page formulaire** : `http://127.0.0.1:8000/bonus/kit-preparation/start`

---

## 🔍 ANALYSE DU FLUX ACTUEL

### ✅ CE QUI EST IMPLÉMENTÉ

#### 1. **Routes et Vues existantes**

**URLs configurées** (`store/urls.py`) :
- `/bonus/kit-preparation/` → `bonus_kit_landing` (page d'accueil)
- `/bonus/kit-preparation/start` → `bonus_kit_start` (formulaire de soumission)
- `/bonus/kit-preparation/merci` → `bonus_kit_thanks` (page de remerciement)

**Template** : `store/templates/store/bonus_prelim_submit.html`
- Formulaire simple avec un textarea pour le texte (≤ 3 pages)
- Soumission via POST

#### 2. **Système de token d'accès**
- Fonction `_make_bonus_token()` : génère un token signé (order_ref + email)
- Fonction `_check_bonus_token()` : vérifie le token (expiration 7 jours)
- Utilisé pour sécuriser l'accès au formulaire

#### 3. **Modèle BonusRequest**
- Modèle complet dans `store/models.py` (lignes 438-488)
- Champs : `uploaded_text`, `docx_path`, `pdf_path`, `status`, etc.
- Statuts : RECEIVED → DRAFTED → READY → SENT

#### 4. **Service de génération DOCX**
- Service `store/services/kit_builder.py` :
  - `build_and_attach_kit()` : génère le DOCX à partir du contenu
  - `build_docx_cover_and_guard()` : crée la couverture
  - `build_docx_content()` : injecte le contenu (intro, Q/R, irrégularités)

#### 5. **Vues Admin (staff only)**
- `bonus_admin_list` : liste des demandes
- `bonus_admin_detail` : détail d'une demande
- `bonus_admin_generate` : génération manuelle du DOCX
- `bonus_admin_download_docx` : téléchargement du Word (staff)

---

### ❌ CE QUI MANQUE / INCOMPLET

#### 1. **Traitement POST dans `bonus_kit_start`**
**Fichier** : `store/views.py` (lignes 1202-1209)

**Problème** : Le traitement POST est incomplet avec un `TODO` :
```python
if request.method == "POST":
    submitted_text = request.POST.get("text") or ""
    # TODO: persister / envoyer email / lancer pipeline…
    return TemplateResponse(...)
```

**Manque** :
- ❌ Création d'un `BonusRequest` en base de données
- ❌ Sauvegarde du texte soumis
- ❌ Lancement de la tâche Celery pour traitement IA
- ❌ Envoi d'email de confirmation

#### 2. **Tâche Celery pour traitement IA**
**Fichier** : `store/tasks.py`

**Problème** : 
- ✅ Tâche `build_kit_word` existe mais est pour `ClientInquiry` (kit complet)
- ❌ **Aucune tâche Celery pour `BonusRequest`**
- ❌ Pas d'intégration OpenAI pour analyser le texte soumis
- ❌ Pas de génération automatique du contenu personnalisé

#### 3. **Vue publique de téléchargement**
**Fichier** : `store/urls.py`

**Problème** :
- ❌ Route `download_bonus_pdf` référencée dans `views_admin_bonus.py` (ligne 289) mais **n'existe pas**
- ❌ Pas de route publique pour télécharger le Word généré
- ❌ Pas de système de lien signé pour les visiteurs (comme pour `kit_download`)

#### 4. **Envoi automatique du lien**
**Fichier** : `store/views_admin_bonus.py` (ligne 289)

**Problème** :
- La fonction `mark_ready_and_send` référence `store:download_bonus_pdf` qui n'existe pas
- Pas d'envoi automatique d'email au client après génération

#### 5. **Intégration IA pour personnalisation**
**Problème** :
- Le service `kit_builder.py` utilise `_build_default_content()` qui génère un contenu par défaut
- ❌ Pas d'analyse du texte soumis par l'IA
- ❌ Pas de personnalisation basée sur le texte du client

---

## 📊 FLUX IDÉAL (ce qui devrait être implémenté)

### Étape 1 : Soumission du formulaire
```
POST /bonus/kit-preparation/start
→ Vérification du token
→ Création d'un BonusRequest
→ Sauvegarde du texte dans uploaded_text
→ Statut: RECEIVED
→ Lancement tâche Celery: build_bonus_kit_word.delay(bonus_request_id)
```

### Étape 2 : Traitement par IA (Celery)
```
Tâche: build_bonus_kit_word(bonus_request_id)
→ Lecture du texte uploadé
→ Appel OpenAI GPT-4 avec le texte
→ Génération du contenu personnalisé (intro, Q/R, irrégularités)
→ Utilisation de kit_builder.build_and_attach_kit()
→ Sauvegarde du DOCX dans docx_path
→ Statut: DRAFTED
```

### Étape 3 : Validation staff (optionnelle)
```
Page admin: /admin/bonus/<pk>/
→ Staff peut revoir le DOCX généré
→ Peut régénérer ou modifier
→ Marquer comme READY
```

### Étape 4 : Envoi au client
```
Action: mark_ready_and_send
→ Génération d'un lien signé (7 jours)
→ Envoi email avec lien de téléchargement
→ Statut: SENT
```

### Étape 5 : Téléchargement par le client
```
GET /bonus/kit-preparation/download/<token>/
→ Vérification du token signé
→ Téléchargement du fichier Word
```

---

## 🔗 URLs ACTUELLES À VISITER

### Pour tester le formulaire :
1. **Page d'accueil** : `http://127.0.0.1:8000/bonus/kit-preparation/`
2. **Formulaire de soumission** : `http://127.0.0.1:8000/bonus/kit-preparation/start?demo=1`
   - Mode démo pour tester sans token

### Pour voir les demandes (staff) :
3. **Liste des demandes** : `http://127.0.0.1:8000/admin/bonus/` (si route configurée)
4. **Détail d'une demande** : `http://127.0.0.1:8000/admin/bonus/<pk>/` (si route configurée)

### ❌ URLs manquantes :
- ❌ `/bonus/kit-preparation/download/<token>/` - Téléchargement public
- ❌ Routes admin non configurées dans `urls.py`

---

## 🛠️ CE QUI DOIT ÊTRE IMPLÉMENTÉ

### 1. **Compléter `bonus_kit_start` (POST)**
```python
# Dans store/views.py, remplacer le TODO :
if request.method == "POST":
    submitted_text = request.POST.get("text") or ""
    
    # Créer BonusRequest
    from store.models import BonusRequest
    from io import BytesIO
    from django.core.files.base import ContentFile
    
    # Créer un fichier temporaire avec le texte
    text_file = ContentFile(submitted_text.encode('utf-8'))
    text_file.name = f"text_{order_ref}.txt"
    
    bonus_request = BonusRequest.objects.create(
        product_slug="audit-sans-peur",
        order_ref=order_ref,
        purchaser_email=email,
        purchaser_name=email.split("@")[0],  # ou récupérer depuis Order
        delivery_email=email,
        service_role="",
        uploaded_text=text_file,
        status="RECEIVED"
    )
    
    # Lancer la tâche Celery
    from store.tasks import build_bonus_kit_word
    build_bonus_kit_word.delay(bonus_request.id)
    
    messages.success(request, "Votre demande est en cours de traitement...")
    return redirect("store:bonus_thanks")
```

### 2. **Créer la tâche Celery `build_bonus_kit_word`**
```python
# Dans store/tasks.py, ajouter :
@shared_task(bind=True, max_retries=3)
def build_bonus_kit_word(self, bonus_request_id):
    """Génère le Word personnalisé pour BonusRequest via IA"""
    from store.models import BonusRequest
    from store.services.kit_builder import build_and_attach_kit
    from openai import OpenAI
    
    br = BonusRequest.objects.get(id=bonus_request_id)
    
    # Lire le texte uploadé
    text_content = br.uploaded_text.read().decode('utf-8')
    
    # Appel OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    # ... génération du contenu personnalisé ...
    
    # Utiliser build_and_attach_kit pour générer le DOCX
    build_and_attach_kit(br, intro_md, qas_list, irregularities_rows)
    
    br.status = "DRAFTED"
    br.save()
```

### 3. **Créer la vue publique de téléchargement**
```python
# Dans store/views.py, ajouter :
def bonus_kit_download(request, token):
    """Téléchargement du Word généré (lien signé, 7 jours)"""
    from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
    from store.models import BonusRequest
    
    signer = TimestampSigner(salt="bonus-kit-download")
    try:
        bonus_request_id = signer.unsign(token, max_age=7 * 24 * 60 * 60)
        br = BonusRequest.objects.get(id=int(bonus_request_id))
    except (SignatureExpired, BadSignature, BonusRequest.DoesNotExist):
        raise Http404("Lien invalide ou expiré.")
    
    if not br.docx_path:
        raise Http404("Document non disponible.")
    
    file_path = Path(settings.PRIVATE_MEDIA_ROOT) / br.docx_path.name
    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=f"kit_{br.pk}.docx"
    )
```

### 4. **Ajouter la route dans `urls.py`**
```python
# Dans store/urls.py, ajouter :
path("bonus/kit-preparation/download/<str:token>/", views.bonus_kit_download, name="bonus_kit_download"),
```

### 5. **Corriger `mark_ready_and_send`**
```python
# Dans store/views_admin_bonus.py, ligne 289 :
download_url = request.build_absolute_uri(
    reverse("store:bonus_kit_download", args=[token])
)
# où token = signer.sign(str(br.pk))
```

### 6. **Configurer les routes admin** (si nécessaire)
```python
# Dans store/urls.py, ajouter :
from . import views_admin_bonus as bonus_admin

path("admin/bonus/", bonus_admin.bonus_admin_list, name="bonus_admin_list"),
path("admin/bonus/<int:pk>/", bonus_admin.bonus_admin_detail, name="bonus_admin_detail"),
path("admin/bonus/<int:pk>/generate/", bonus_admin.bonus_admin_generate, name="bonus_admin_generate"),
path("admin/bonus/<int:pk>/download/", bonus_admin.bonus_admin_download_docx, name="bonus_admin_download"),
```

---

## 📝 RÉSUMÉ

### ✅ EXISTE
- ✅ Formulaire de soumission (`/bonus/kit-preparation/start`)
- ✅ Modèle `BonusRequest` complet
- ✅ Service de génération DOCX (`kit_builder.py`)
- ✅ Vues admin pour gestion manuelle
- ✅ Système de token d'accès

### ❌ MANQUE
- ❌ Traitement POST complet (création BonusRequest + lancement Celery)
- ❌ Tâche Celery pour traitement IA automatique
- ❌ Vue publique de téléchargement
- ❌ Route de téléchargement dans `urls.py`
- ❌ Envoi automatique d'email avec lien
- ❌ Intégration IA pour personnalisation du contenu

### 🎯 PROCHAINES ÉTAPES
1. Compléter le traitement POST dans `bonus_kit_start`
2. Créer la tâche Celery `build_bonus_kit_word`
3. Créer la vue publique `bonus_kit_download`
4. Ajouter les routes manquantes
5. Tester le flux complet

---

**Date de l'analyse** : 2025-01-XX
**Fichiers clés** :
- `store/views.py` (lignes 1185-1213)
- `store/tasks.py` (ligne 20 - build_kit_word pour ClientInquiry)
- `store/models.py` (lignes 438-488 - BonusRequest)
- `store/services/kit_builder.py`
- `store/urls.py`

