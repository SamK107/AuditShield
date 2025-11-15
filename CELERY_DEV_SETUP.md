# Configuration Celery pour le Développement

## Problème
Celery ne peut pas se connecter à Redis car Redis n'est pas démarré ou disponible.

## Solutions

### ✅ Solution 1 : Exécution synchrone (RECOMMANDÉE pour le dev)

**La plus simple** : Les tâches s'exécutent immédiatement sans worker ni Redis.

Dans `config/settings/dev.py`, décommentez cette ligne :

```python
CELERY_TASK_ALWAYS_EAGER = True  # Exécute les tâches immédiatement
```

**Avantages** :
- ✅ Pas besoin de Redis
- ✅ Pas besoin de démarrer un worker Celery
- ✅ Les tâches s'exécutent immédiatement lors de la soumission
- ✅ Plus facile à déboguer

**Inconvénients** :
- ⚠️ Les tâches bloquent la réponse HTTP (mais c'est OK pour le dev)
- ⚠️ Pas de traitement asynchrone

### ✅ Solution 2 : Utiliser la base de données comme broker

Celery utilise PostgreSQL comme broker (pas besoin de Redis).

**Prérequis** : Installer `kombu[db]`
```bash
pip install "kombu[db]"
```

**Configuration** : Déjà configurée dans `dev.py` (lignes 131-144)

**Démarrer le worker** :
```bash
celery -A config worker -l info -P solo
```

### ✅ Solution 3 : Utiliser Redis (production)

**Installer Redis sur Windows** :
1. Télécharger depuis : https://github.com/microsoftarchive/redis/releases
2. Ou utiliser WSL : `wsl sudo apt-get install redis-server`
3. Démarrer Redis : `redis-server`

**Démarrer le worker** :
```bash
celery -A config worker -l info -P solo
```

### ✅ Solution 4 : Utiliser la commande process_kit_tasks (sans Celery)

**Alternative sans Celery** : Utiliser la commande de gestion Django.

**Créer les tâches manquantes** :
```bash
python manage.py create_missing_kit_tasks
```

**Traiter les tâches** :
```bash
python manage.py process_kit_tasks
```

**Avantages** :
- ✅ Pas besoin de Celery/Redis
- ✅ Plus simple à comprendre
- ✅ Fonctionne avec notre système `KitProcessingTask`

---

## Recommandation pour le développement

**Utilisez la Solution 1** (CELERY_TASK_ALWAYS_EAGER = True) :
- Simple et rapide
- Pas de configuration supplémentaire
- Parfait pour tester

**Pour la production**, utilisez Redis avec un worker Celery.

