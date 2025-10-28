# Guide de Robustesse - Pages d'Erreur Django

## Date
October 21, 2025

## Objectif
Garantir que les pages d'erreur 404 et 500 ne plantent **jamais**, même si :
- Des URLs sont manquantes ou mal configurées
- Des namespaces Django sont incorrects
- Des erreurs surviennent durant le rendering des templates

## Problème résolu

### Avant (fragile)
```html
<!-- templates/404.html - FRAGILE -->
{% extends "base.html" %}
{% block content %}
  <a href="{% url 'store:offers' %}">Voir les offres</a>
  <!-- ⚠️ Si 'store:offers' n'existe pas → NoReverseMatch → 500 au lieu de 404 -->
{% endblock %}
```

**Conséquences** :
- Une erreur 404 se transforme en erreur 500
- L'utilisateur voit une page générique Django au lieu de notre belle page personnalisée
- Les logs sont pollués avec des erreurs de template

### Après (robuste)
```html
<!-- templates/404.html - ROBUSTE -->
{% extends "base.html" %}

{# Override footer to avoid {% url %} #}
{% block footer_links %}
  <nav class="flex items-center gap-4">
    <a href="/" class="hover:underline">Accueil</a>
    <a href="/offres/" class="hover:underline">Offres</a>
  </nav>
{% endblock %}

{% block content %}
  <a href="/">Retour à l'accueil</a>
  <a href="/offres/">Voir les offres</a>
  <!-- ✅ Liens hardcodés → toujours fonctionnels -->
{% endblock %}
```

## Architecture des templates d'erreur

```
base.html (global layout)
    ├── {% block footer_links %}  ← Surcharge possible
    │       └── Liens avec {% url %} (pour pages normales)
    │
    └── {% block content %}
            └── Contenu de la page

404.html / 500.html
    ├── {% block footer_links %}  ← Surcharge avec hrefs hardcodés
    │       └── Liens hardcodés (pas de {% url %})
    │
    └── {% block content %}
            └── Liens hardcodés (pas de {% url %})
```

## Fichiers modifiés

### 1. `templates/base.html`
**Changement** : Ajout du bloc `footer_links` surchargeabl

```html
{% block site_footer %}
  <footer class="...">
    <div>© ...</div>
    
    {# IMPORTANT: Bloc surcharegeable pour éviter {% url %} dans les erreurs #}
    {% block footer_links %}
      <nav>
        <a href="{% url 'legal:mentions' %}">Mentions légales</a>
        <a href="{% url 'legal:privacy' %}">Confidentialité</a>
        <!-- Etc. -->
      </nav>
    {% endblock footer_links %}
  </footer>
{% endblock site_footer %}
```

### 2. `templates/404.html`
**Changements** :
- Override du bloc `footer_links` avec des hrefs hardcodés
- Liens de navigation hardcodés dans le contenu
- Aucun `{% url %}` dans le template

```html
{% extends "base.html" %}
{% block title %}Page introuvable (404){% endblock %}

{# Override footer pour éviter NoReverseMatch #}
{% block footer_links %}
  <nav class="flex items-center gap-4">
    <a href="/" class="hover:underline">Accueil</a>
    <a href="/offres/" class="hover:underline">Offres</a>
  </nav>
{% endblock %}

{% block content %}
  <div class="error-page">
    <h1>Oups — page introuvable</h1>
    <p>Le contenu demandé n'existe pas...</p>
    <a href="/">Retour à l'accueil</a>
    <a href="/offres/">Voir les offres</a>
  </div>
{% endblock %}
```

### 3. `templates/500.html`
**Changements** : Identiques à 404.html
- Override de `footer_links`
- Liens hardcodés
- Aucun `{% url %}`

### 4. `templates/base_error_min.html` (fallback optionnel)
**Usage** : Template ultra-minimal en cas de besoin absolu
- Pas d'héritage
- CSS inline ou liens statiques hardcodés
- Utilisable en changeant `{% extends "base.html" %}` en `{% extends "base_error_min.html" %}`

```html
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>{% block title %}Erreur{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/app.build.css" />
</head>
<body>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

## Configuration Django

### Error Handlers (`config/urls.py`)
```python
# Définir les handlers personnalisés
handler404 = "core.views.custom_404"
handler500 = "core.views.custom_500"
```

### Vues d'erreur (`core/views.py`)
```python
def custom_404(request, exception, template_name="404.html"):
    """Custom 404 handler - toujours safe"""
    return render(request, template_name, status=404)

def custom_500(request, template_name="500.html"):
    """Custom 500 handler - toujours safe"""
    return render(request, template_name, status=500)
```

## Test des pages d'erreur

### Configuration pour les tests
```python
# config/settings/dev.py
DEBUG = False  # Mettre temporairement à False pour tester les erreurs
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### Tests à effectuer

#### 1. Test 404 (page introuvable)
```bash
# Lancer le serveur
python manage.py runserver

# Visiter une URL qui n'existe pas
http://127.0.0.1:8000/cette-page-nexiste-pas/

# ✅ Devrait afficher templates/404.html avec le design personnalisé
```

#### 2. Test 500 (erreur serveur)
```bash
# Visiter la route de test (temporaire)
http://127.0.0.1:8000/boom/

# ✅ Devrait afficher templates/500.html avec le design personnalisé
```

#### 3. Test avec URLs cassées
Pour tester la robustesse, vous pouvez temporairement :
```python
# Dans config/urls.py - commenter une app
urlpatterns = [
    # path("", include(("store.urls", "store"), namespace="store")),  # commenté
    ...
]

# Les pages 404/500 doivent quand même s'afficher correctement
# car elles n'utilisent pas {% url 'store:...' %}
```

### Nettoyage après test

1. **Remettre DEBUG=True** dans `config/settings/dev.py`
2. **Supprimer la route de test** :
   - Retirer `path("boom/", views.boom, name="boom")` de `core/urls.py`
   - Retirer la fonction `boom()` de `core/views.py`

## Bonnes pratiques

### ✅ À FAIRE dans les pages d'erreur

1. **Utiliser des hrefs hardcodés**
   ```html
   <a href="/">Accueil</a>
   <a href="/offres/">Offres</a>
   ```

2. **Override le bloc footer_links**
   ```html
   {% block footer_links %}
     <nav>
       <a href="/">Accueil</a>
     </nav>
   {% endblock %}
   ```

3. **Tester en DEBUG=False**
   - Les pages d'erreur ne sont visibles qu'avec `DEBUG=False`
   - En développement, Django montre des pages de debug détaillées

### ❌ À ÉVITER dans les pages d'erreur

1. **NE PAS utiliser {% url %}**
   ```html
   <!-- ❌ MAUVAIS -->
   <a href="{% url 'store:offers' %}">Offres</a>
   
   <!-- ✅ BON -->
   <a href="/offres/">Offres</a>
   ```

2. **NE PAS charger des objets depuis la DB**
   ```python
   # ❌ MAUVAIS dans custom_404
   def custom_404(request, exception):
       products = Product.objects.all()  # Peut échouer si DB down
       return render(request, "404.html", {"products": products})
   
   # ✅ BON
   def custom_404(request, exception):
       return render(request, "404.html", status=404)
   ```

3. **NE PAS faire de requêtes externes**
   - Pas d'appels API
   - Pas de connexions réseau
   - Gardez les pages d'erreur 100% statiques

## Correspondance URLs

Pour référence, voici les URLs actuelles du projet :

| Href hardcodé | URL Django équivalente | Namespace |
|---------------|------------------------|-----------|
| `/` | `{% url 'core:coming_soon' %}` | core:coming_soon |
| `/accueil/` | `{% url 'core:home' %}` | core:home |
| `/offres/` | `{% url 'store:offers' %}` | store:offers |
| `/exemples/` | `{% url 'store:examples' %}` | store:examples |
| `/a-propos/` | `{% url 'core:about' %}` | core:about |
| `/mentions-legales/` | `{% url 'legal:mentions' %}` | legal:mentions |
| `/privacy/` | `{% url 'legal:privacy' %}` | legal:privacy |
| `/cookies/` | `{% url 'legal:cookies' %}` | legal:cookies |

**Note** : Les pages d'erreur utilisent les hrefs hardcodés pour garantir qu'elles fonctionnent toujours.

## Avantages de cette approche

✅ **Fiabilité maximale**
- Les pages d'erreur ne peuvent pas planter
- Aucune dépendance sur les URL patterns
- Fonctionnent même si la configuration Django est cassée

✅ **Maintenance facilitée**
- Un seul endroit à mettre à jour : `footer_links` dans base.html
- Les pages normales utilisent toujours `{% url %}`
- Les pages d'erreur override uniquement ce qui est nécessaire

✅ **Expérience utilisateur**
- Toujours une page d'erreur élégante
- Jamais de page Django générique
- Navigation fonctionnelle même en cas d'erreur

✅ **Debugging simplifié**
- Les logs montrent la vraie erreur (404/500)
- Pas d'erreur secondaire de template
- Stack traces propres

## Résumé

Cette architecture garantit que vos pages d'erreur sont **indestructibles** :

1. **`base.html`** : Layout normal avec `{% url %}` et bloc `footer_links` surcharegeable
2. **`404.html` / `500.html`** : Override `footer_links` avec hrefs hardcodés, pas de `{% url %}`
3. **`base_error_min.html`** : Fallback ultra-minimal (optionnel)
4. **Custom handlers** : Simples, sans logique métier

Résultat : **Vos utilisateurs voient toujours une belle page d'erreur, jamais une erreur Django générique.** 🎉

