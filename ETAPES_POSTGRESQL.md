# Étapes pour finaliser la migration vers PostgreSQL 13.22

## ✅ Déjà fait
- Base de données `auditshield` créée
- Configuration `.env` et `dev.py` renseignée (lignes 7-11)
- Environnement virtuel `.venv` activé
- Dépendances PostgreSQL (`psycopg2-binary`) installées
- ✅ Connexion à la base de données testée et validée
- ✅ Migration corrigée (CheckConstraint dans store/migrations/0015)
- ✅ Migrations pour `core` créées
- ✅ Toutes les migrations appliquées avec succès
- ✅ Fichiers statiques collectés

## 📋 Étapes suivantes à exécuter

### 1. Tester la connexion à la base de données
```powershell
cd auditshield
python manage.py check --database default
```

### 2. Vérifier les migrations existantes
```powershell
python manage.py showmigrations
```

### 3. Créer les migrations pour l'app `core` (si nécessaire)
L'app `core` n'a pas de dossier `migrations`. Si elle contient des modèles, il faut créer les migrations :
```powershell
python manage.py makemigrations core
```

### 4. Appliquer toutes les migrations
```powershell
python manage.py migrate
```

Cette commande va créer toutes les tables dans PostgreSQL pour :
- `store` (15 migrations)
- `downloads` (10 migrations)
- `legal` (2 migrations)
- `core` (si des migrations ont été créées)
- Les apps Django par défaut (auth, sessions, etc.)

### 5. Créer un superutilisateur Django
```powershell
python manage.py createsuperuser
```

Suivez les instructions pour créer un compte administrateur.

### 6. Collecter les fichiers statiques
```powershell
python manage.py collectstatic --noinput
```

### 7. Lancer le serveur de développement
```powershell
python manage.py runserver
```

Le serveur sera accessible sur `http://127.0.0.1:8000`

## 🔍 Vérifications supplémentaires

### Vérifier que les tables sont créées dans PostgreSQL
Vous pouvez vous connecter à PostgreSQL et vérifier :
```sql
\c auditshield
\dt
```

### Vérifier les logs Django
Si des erreurs apparaissent, vérifiez les logs dans `logs/app.log`

## ⚠️ Notes importantes

- Assurez-vous que PostgreSQL 13.22 est bien démarré
- Vérifiez que les identifiants dans `.env` sont corrects :
  - `DB_NAME=auditshield`
  - `DB_USER=...`
  - `DB_PASSWORD=...`
  - `DB_HOST=127.0.0.1` (ou `localhost`)
  - `DB_PORT=5432` (ou le port de votre installation PostgreSQL)

## 🐛 En cas de problème

### Erreur de connexion
- Vérifiez que PostgreSQL est démarré
- Vérifiez les identifiants dans `.env`
- Testez la connexion avec `psql -U votre_user -d auditshield`

### Erreur de migrations
- Si des migrations sont en conflit : `python manage.py migrate --fake-initial`
- Pour réinitialiser : supprimez les tables et relancez `migrate`

### Erreur de permissions
- Assurez-vous que l'utilisateur PostgreSQL a les droits sur la base `auditshield`

