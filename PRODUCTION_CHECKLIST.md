# ✅ Checklist Production - Layout Global + Pages d'Erreur

## Avant de déployer en production

### 1. Nettoyage du code de test
- [ ] Supprimer `path("boom/", views.boom, name="boom")` dans `core/urls.py`
- [ ] Supprimer la fonction `boom()` dans `core/views.py`
- [ ] Supprimer les commentaires de test ajoutés

### 2. Configuration production
- [ ] `DEBUG = False` dans `config/settings/prod.py`
- [ ] `ALLOWED_HOSTS` contient les domaines de production
- [ ] `SECRET_KEY` est unique et sécurisée (pas la clé de dev)
- [ ] Variables d'environnement configurées (`.env` en prod)

### 3. Tests fonctionnels
- [ ] Tester la page d'accueil `/`
- [ ] Tester les offres `/offres/`
- [ ] Tester une page 404 (URL inexistante)
- [ ] Tester tous les liens du footer
- [ ] Vérifier que les images/CSS/JS se chargent

### 4. Collecte des fichiers statiques
```bash
python manage.py collectstatic --noinput
```
- [ ] Commande exécutée avec succès
- [ ] Fichiers dans `staticfiles/` (ou selon config)
- [ ] Whitenoise activé (si utilisé)

### 5. Base de données
```bash
python manage.py migrate --check
python manage.py migrate
```
- [ ] Toutes les migrations appliquées
- [ ] Aucune migration en attente

### 6. Sécurité
- [ ] `SECURE_SSL_REDIRECT = True` en prod
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS` configuré (86400 minimum)

### 7. Pages d'erreur (test final)
Avec `DEBUG=False` :
- [ ] `/page-inexistante/` → affiche 404.html
- [ ] Vérifier qu'aucun `{% url %}` ne cause d'erreur
- [ ] Footer fonctionne avec hrefs hardcodés

### 8. Monitoring et logs
- [ ] Logging configuré (fichier ou Sentry)
- [ ] Erreurs 500 sont loggées
- [ ] Email admins configuré (optionnel)

### 9. Performance
- [ ] Compression Whitenoise activée
- [ ] Cache configuré (si applicable)
- [ ] `CONN_MAX_AGE` configuré pour DB

### 10. Documentation
- [ ] `ROBUSTNESS_GUIDE.md` lu et compris
- [ ] `REFACTORING_SUMMARY.md` parcouru
- [ ] Équipe informée des changements

---

## Commandes rapides

```bash
# Activer l'environnement virtuel
.\Active-le\Scripts\Activate.ps1

# Collecter les statiques
python manage.py collectstatic --noinput

# Vérifier les migrations
python manage.py migrate --check

# Lancer le serveur de test (DEBUG=False)
python manage.py runserver

# Tester une 404
curl http://localhost:8000/inexistant

# Lancer en production (avec gunicorn par exemple)
gunicorn config.wsgi:application
```

---

## Post-déploiement

### Vérifications immédiates
- [ ] Site accessible depuis le domaine de production
- [ ] HTTPS fonctionne correctement
- [ ] Pages principales se chargent
- [ ] Test d'une URL 404
- [ ] Footer et navigation fonctionnels

### Monitoring (premières 24h)
- [ ] Surveiller les logs d'erreur
- [ ] Vérifier les requêtes 404/500
- [ ] Tester depuis différents navigateurs
- [ ] Tester depuis mobile

---

## En cas de problème

### Rollback rapide
Si un problème majeur survient :
1. Revenir à la version précédente du code
2. Redéployer l'ancienne version
3. Investiguer le problème en staging

### Debug en production (avec précaution)
```python
# Ne JAMAIS faire ça longtemps !
DEBUG = True  # Temporaire pour debug
```
⚠️ Remettre `DEBUG = False` dès que possible !

### Contacts
- Admin système : [À remplir]
- Développeur principal : [À remplir]
- Hébergeur : [À remplir]

---

*Checklist mise à jour le 21 octobre 2025*

