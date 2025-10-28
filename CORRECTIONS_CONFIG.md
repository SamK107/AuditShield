# Corrections apportées à la configuration Django

## Résumé des changements

### 1. Fichiers de configuration créés/modifiés

#### ✅ `config/settings/base.py`
- Configuration de base complète avec toutes les applications (core, store, downloads, legal)
- Support de WhiteNoise pour les fichiers statiques
- Configuration CinetPay
- Configuration email
- Lecture du fichier `.env` avec `environs`
- Tous les paramètres partagés entre dev et prod

#### ✅ `config/settings/dev.py`
- Configuration spécifique au développement
- **PostgreSQL au lieu de SQLite** (comme demandé)
- DEBUG = True
- Email backend console
- Logging verbeux avec affichage des requêtes SQL
- Sécurité désactivée pour le développement local

#### ✅ `config/settings/prod.py`
- Configuration spécifique à la production
- PostgreSQL avec pool de connexions
- Sécurité renforcée (HTTPS, HSTS, cookies sécurisés)
- Logging dans des fichiers avec rotation
- Configuration adaptée pour LWS/proxy

#### ✅ `.env` (créé depuis ENV_TEMPLATE.txt)
```env
DB_NAME=auditdb
DB_USER=auditshield
DB_PASSWORD=tata1000@
DB_HOST=127.0.0.1
DB_PORT=5432
```

## ⚠️ Problème actuel

**Erreur d'authentification PostgreSQL** : 
```
FATAL: authentification par mot de passe échouée pour l'utilisateur "auditshield"
```

## 🔧 Solutions à tester

### Solution 1 : Vérifier les identifiants PostgreSQL

Ouvrez pgAdmin ou psql et exécutez :

```sql
-- Vérifier si l'utilisateur existe
SELECT usename FROM pg_user WHERE usename = 'auditshield';

-- Si l'utilisateur n'existe pas, le créer
CREATE USER auditshield WITH PASSWORD 'tata1000@';

-- Donner les droits sur la base de données
GRANT ALL PRIVILEGES ON DATABASE auditdb TO auditshield;

-- Si la base n'existe pas, la créer
CREATE DATABASE auditdb OWNER auditshield;
```

### Solution 2 : Vérifier pg_hba.conf

Le fichier `pg_hba.conf` doit permettre l'authentification par mot de passe :

1. Localisez le fichier (souvent dans `C:\Program Files\PostgreSQL\15\data\pg_hba.conf`)
2. Ajoutez ou modifiez cette ligne :
   ```
   # TYPE  DATABASE    USER         ADDRESS       METHOD
   host    auditdb     auditshield  127.0.0.1/32  md5
   ```
3. Redémarrez PostgreSQL

### Solution 3 : Utiliser psql pour tester

```bash
psql -U auditshield -d auditdb -h 127.0.0.1 -W
```

Si cela fonctionne, Django devrait aussi fonctionner.

### Solution 4 : Modifier temporairement le mot de passe

Si le caractère `@` pose problème, essayez un mot de passe simple :

```sql
ALTER USER auditshield WITH PASSWORD 'tata1000';
```

Puis modifiez `.env` :
```env
DB_PASSWORD=tata1000
```

## ✅ Tests de validation

Une fois PostgreSQL configuré, exécutez :

```powershell
# 1. Vérifier la configuration Django
cd auditshield
.\.venv\Scripts\Activate.ps1
python manage.py check

# 2. Créer les tables
python manage.py migrate

# 3. Créer un superutilisateur
python manage.py createsuperuser

# 4. Lancer le serveur
python manage.py runserver
```

## 📋 Structure finale des settings

```
config/
├── settings/
│   ├── __init__.py
│   ├── base.py      # Configuration partagée
│   ├── dev.py       # Dev avec PostgreSQL
│   └── prod.py      # Production
├── settings.py      # Ancienne config (peut être conservée)
└── urls.py
```

## 🔄 Utilisation

### Développement
```bash
# Dans .env
DJANGO_SETTINGS_MODULE=config.settings.dev

# Ou dans la ligne de commande
python manage.py runserver --settings=config.settings.dev
```

### Production
```bash
# Dans .env
DJANGO_SETTINGS_MODULE=config.settings.prod
```

## 📝 Notes importantes

1. **Le fichier `.env` n'est pas versionné** (dans .gitignore)
2. **ENV_TEMPLATE.txt contient le template** à copier pour créer `.env`
3. **SQLite n'est plus utilisé** - uniquement PostgreSQL en dev et prod
4. **Les erreurs de linter ont été corrigées** dans tous les fichiers
5. **La configuration est modulaire** : base.py + (dev.py | prod.py)

## 🎯 Prochaines étapes

1. ✅ Configuration Django OK
2. ⚠️ **Résoudre l'authentification PostgreSQL** (voir solutions ci-dessus)
3. ⏭️ Exécuter les migrations
4. ⏭️ Tester l'application

---

**Date des corrections** : {{ date }}
**Fichiers modifiés** : 4 (base.py, dev.py, prod.py, .env)
**Fichiers créés** : 2 (ENV_TEMPLATE.txt, CORRECTIONS_CONFIG.md)

