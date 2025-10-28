# 📧 Command fetch_receipts - Guide d'utilisation

## 🎯 Objectif

Cette commande traite automatiquement les emails reçus sur `receipts@auditsanspeur.com` pour créer des `ExternalEntitlement` dans la base de données.

## 🚀 Utilisation

### Mode par défaut (UNSEEN seulement)
Traite uniquement les emails **non lus** :
```bash
python manage.py fetch_receipts
```

### Mode complet (tous les emails)
Traite **tous les emails** (y compris ceux déjà lus) :
```bash
python manage.py fetch_receipts --all
```

### Avec verbosité
```bash
python manage.py fetch_receipts -v 3
python manage.py fetch_receipts --all -v 3
```

## ⚙️ Fonctionnement

1. **Connexion IMAP** à la boîte `receipts@auditsanspeur.com`
2. **Recherche** des emails avec référence de commande (EXT-*, REF-*, etc.)
3. **Extraction** de la référence et de l'email expéditeur
4. **Création/Mise à jour** d'un `ExternalEntitlement` dans la base
5. **Déplacement** de l'email traité dans le dossier "Processed"
6. **Marquage** de l'email comme lu (\Seen)

## 🔧 Configuration

Variables d'environnement requises :
- `RECEIPTS_IMAP_HOST` (défaut: `imap.auditsanspeur.com`)
- `RECEIPTS_IMAP_PORT` (défaut: `993`)
- `RECEIPTS_IMAP_USER` (email IMAP)
- `RECEIPTS_IMAP_PASSWORD` (mot de passe IMAP)
- `RECEIPTS_IMAP_FOLDER` (défaut: `INBOX`)

## 🔄 Automatisation

### Option 1 : Cron (Linux/Mac)
Ajouter dans crontab :
```bash
# Toutes les 15 minutes
*/15 * * * * cd /path/to/auditshield && .venv/bin/python manage.py fetch_receipts >> /var/log/fetch_receipts.log 2>&1
```

### Option 2 : Planificateur de tâches Windows
Créer une tâche planifiée qui exécute :
```powershell
cd C:\path\to\auditshield
.venv\Scripts\python.exe manage.py fetch_receipts
```

### Option 3 : Django-Q / Celery Beat
Utiliser un gestionnaire de tâches Django pour planifier l'exécution.

## ⚠️ Problème courant : Email déjà traité

Si un email avec `EXT-7777` a été envoyé mais n'apparaît pas dans la base :

1. **Vérifier si l'email a été marqué comme lu** :
   ```bash
   python manage.py fetch_receipts --all -v 3
   ```

2. **Vérifier les entitlements existants** :
   ```python
   from downloads.models import ExternalEntitlement
   ExternalEntitlement.objects.filter(order_ref__iexact="EXT-7777")
   ```

3. **Si l'email est déjà dans "Processed"**, il ne sera pas retraité automatiquement. Il faudra le replacer dans INBOX ou créer manuellement l'entitlement.

## 📝 Notes

- La commande utilise `UNSEEN` par défaut pour éviter les doublons
- Les emails traités sont déplacés dans le dossier "Processed"
- La catégorie par défaut est la première catégorie disponible (ordre croissant)
- Les références sont normalisées en majuscules (EXT-12345)

