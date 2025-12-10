# 🔴 Installation et Configuration de Redis

Redis est nécessaire pour Celery (tâches asynchrones). Voici 3 méthodes d'installation pour Windows.

---

## 📋 Méthode Recommandée : Docker (La Plus Simple)

### Prérequis : Docker Desktop

Si Docker n'est pas installé :

1. **Téléchargez** : https://www.docker.com/products/docker-desktop
2. **Installez** Docker Desktop pour Windows
3. **Lancez** Docker Desktop
4. **Attendez** que Docker démarre (icône Docker dans la barre des tâches)

### Installation Redis via Docker

```bash
# Lancer Redis (une seule commande !)
docker run -d -p 6379:6379 --name auditshield-redis redis:alpine
```

**Explication :**
- `-d` : Mode détaché (tourne en arrière-plan)
- `-p 6379:6379` : Expose le port 6379 (port standard Redis)
- `--name auditshield-redis` : Nom du conteneur
- `redis:alpine` : Image Redis légère (30 MB)

### Vérification

```bash
# Vérifier que Redis tourne
docker ps
```

**Résultat attendu :**
```
CONTAINER ID   IMAGE          STATUS         PORTS                    NAMES
abc123def456   redis:alpine   Up 2 minutes   0.0.0.0:6379->6379/tcp   auditshield-redis
```

### Test de Connexion

```bash
# Option 1 : Via Docker
docker exec -it auditshield-redis redis-cli ping
# Devrait retourner : PONG

# Option 2 : Via Python (dans le shell Django)
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

Dans le shell Python :
```python
import redis

# Test de connexion
r = redis.Redis(host='localhost', port=6379, db=0)
print(r.ping())  # Devrait afficher : True

exit()
```

### Commandes Utiles Docker

```bash
# Arrêter Redis
docker stop auditshield-redis

# Démarrer Redis (après arrêt)
docker start auditshield-redis

# Voir les logs Redis
docker logs auditshield-redis

# Redémarrer Redis
docker restart auditshield-redis

# Supprimer le conteneur (pour réinstaller)
docker rm -f auditshield-redis
```

### Configuration Automatique au Démarrage

Pour que Redis démarre automatiquement avec Windows :

```bash
docker update --restart=always auditshield-redis
```

---

## 📋 Méthode Alternative 1 : WSL2 (Windows Subsystem for Linux)

### Prérequis : WSL2 installé

Si WSL n'est pas installé :

```powershell
# Dans PowerShell (Admin)
wsl --install
# Redémarrer Windows après installation
```

### Installation Redis dans WSL

```bash
# Ouvrir WSL (Ubuntu)
wsl

# Mettre à jour les packages
sudo apt update

# Installer Redis
sudo apt install redis-server -y

# Éditer la configuration (optionnel)
sudo nano /etc/redis/redis.conf
# Recherchez "supervised" et changez en : supervised systemd

# Démarrer Redis
sudo service redis-server start

# Vérifier
redis-cli ping
# Devrait retourner : PONG
```

### Démarrage Automatique

Pour démarrer Redis automatiquement avec WSL :

```bash
# Ajouter au ~/.bashrc
echo "sudo service redis-server start" >> ~/.bashrc
```

### Commandes Utiles WSL

```bash
# Démarrer Redis
sudo service redis-server start

# Arrêter Redis
sudo service redis-server stop

# Redémarrer Redis
sudo service redis-server restart

# Statut
sudo service redis-server status

# Voir les logs
sudo tail -f /var/log/redis/redis-server.log
```

---

## 📋 Méthode Alternative 2 : Redis Windows (Memurai)

Memurai est un port natif de Redis pour Windows.

### Installation

1. **Téléchargez** : https://www.memurai.com/get-memurai
2. **Installez** l'exe téléchargé
3. **Suivez** l'assistant d'installation
4. **Redis démarre automatiquement** comme service Windows

### Vérification

```bash
# Dans PowerShell ou CMD
redis-cli ping
# Devrait retourner : PONG
```

### Gestion du Service

```powershell
# Arrêter Redis
net stop Memurai

# Démarrer Redis
net start Memurai

# Statut
sc query Memurai
```

---

## 🔧 Configuration dans AuditShield

### Vérifier le fichier `.env`

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield"
notepad .env
```

**Vérifiez/ajoutez** :
```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Si Redis tourne sur un autre port ou machine :**
```bash
# Exemple : Redis sur le port 6380
CELERY_BROKER_URL=redis://localhost:6380/0

# Exemple : Redis sur une autre machine
CELERY_BROKER_URL=redis://192.168.1.100:6379/0
```

### Vérification dans Django

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

```python
from django.conf import settings
import redis

# Vérifier la configuration
broker_url = settings.CELERY_BROKER_URL
print(f"Celery Broker : {broker_url}")

# Test de connexion
try:
    # Extraire host et port de l'URL
    import re
    match = re.match(r'redis://([^:]+):(\d+)', broker_url)
    if match:
        host, port = match.groups()
        r = redis.Redis(host=host, port=int(port), db=0)
        if r.ping():
            print("✅ Redis fonctionne !")
        else:
            print("❌ Redis ne répond pas")
    else:
        print("⚠️  URL Redis mal formatée")
except Exception as e:
    print(f"❌ Erreur : {e}")

exit()
```

---

## 🧪 Test Complet avec Celery

### 1. Démarrer Redis (choisir une méthode ci-dessus)

```bash
# Docker (recommandé)
docker start auditshield-redis

# Ou WSL
wsl
sudo service redis-server start

# Ou Memurai (déjà démarré automatiquement)
```

### 2. Démarrer Celery Worker

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield

# Démarrer Celery
celery -A config worker -l info
```

**Sortie attendue :**
```
 -------------- celery@VOTRE-PC v5.3.x
---- **** ----- 
--- * ***  * -- Windows-10-...
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         config:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: OFF
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . store.tasks.run_kit_ai_pipeline
  . store.tasks.build_kit_word
  ...

[2025-12-07 14:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-12-07 14:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-12-07 14:00:00,000: INFO/MainProcess] mingle: all alone
[2025-12-07 14:00:00,000: INFO/MainProcess] celery@VOTRE-PC ready.
```

✅ **Si vous voyez "celery@... ready." → SUCCÈS !**

### 3. Test d'une Tâche

Dans un **nouveau terminal** (pendant que Celery tourne) :

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

```python
from celery import current_app

# Envoyer une tâche de test
result = current_app.send_task('celery.ping')
print(f"Tâche envoyée : {result.id}")

# Vérifier dans le terminal Celery
# Vous devriez voir : [INFO] Task celery.ping[...] received
```

---

## 🐛 Dépannage

### Erreur : "Cannot connect to redis"

**Causes possibles :**

1. **Redis n'est pas démarré**
   ```bash
   # Docker
   docker ps | Select-String redis
   # Si vide, démarrer : docker start auditshield-redis
   
   # WSL
   wsl redis-cli ping
   ```

2. **Mauvais port dans `.env`**
   ```bash
   # Vérifier le port Redis
   redis-cli -p 6379 ping
   
   # Si erreur, Redis est sur un autre port
   # Chercher : netstat -an | Select-String 6379
   ```

3. **Firewall bloque le port**
   ```powershell
   # Autoriser le port (PowerShell Admin)
   New-NetFirewallRule -DisplayName "Redis" -Direction Inbound -Protocol TCP -LocalPort 6379 -Action Allow
   ```

### Erreur : "redis-cli: command not found"

**Solution pour Docker :**
```bash
docker exec -it auditshield-redis redis-cli ping
```

**Solution pour WSL :**
```bash
wsl redis-cli ping
```

**Installer redis-tools (Windows) :**
```bash
# Via Chocolatey
choco install redis-cli

# Ou télécharger depuis GitHub
# https://github.com/microsoftarchive/redis/releases
```

### Celery ne se connecte pas

**Vérifier l'URL dans `.env` :**
```bash
# Doit être exactement :
CELERY_BROKER_URL=redis://localhost:6379/0

# Pas d'espace, pas de guillemets
```

**Test manuel Python :**
```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.set('test', 'hello')
print(r.get('test'))  # Doit afficher : hello
r.delete('test')
```

### Redis plante ou ne démarre pas

**Docker :**
```bash
# Voir les logs
docker logs auditshield-redis

# Recréer le conteneur
docker rm -f auditshield-redis
docker run -d -p 6379:6379 --name auditshield-redis redis:alpine
```

**WSL :**
```bash
# Voir les logs
sudo tail -50 /var/log/redis/redis-server.log

# Reconfigurer
sudo apt remove --purge redis-server
sudo apt install redis-server
```

---

## 📊 Monitoring Redis

### Voir les informations Redis

```bash
redis-cli info
```

### Voir les clés Celery

```bash
redis-cli
> KEYS celery*
> KEYS *
> exit
```

### Vider Redis (si nécessaire)

```bash
redis-cli FLUSHALL
```

⚠️ **Attention** : Ceci supprime TOUTES les données Redis !

---

## 🔒 Sécurité (Production)

Pour la production, sécurisez Redis :

### 1. Mot de passe Redis

Éditez la config :
```bash
# Docker
docker exec -it auditshield-redis redis-cli CONFIG SET requirepass "VotreMotDePasseSecure"

# WSL
sudo nano /etc/redis/redis.conf
# Ajoutez : requirepass VotreMotDePasseSecure
sudo service redis-server restart
```

Mettez à jour `.env` :
```bash
CELERY_BROKER_URL=redis://:VotreMotDePasseSecure@localhost:6379/0
```

### 2. Limiter l'accès réseau

```bash
# Docker : bind seulement localhost
docker run -d -p 127.0.0.1:6379:6379 --name auditshield-redis redis:alpine

# WSL : dans redis.conf
bind 127.0.0.1
```

---

## ✅ Checklist Finale

- [ ] Redis installé (Docker / WSL / Memurai)
- [ ] Redis démarre : `docker ps` ou `redis-cli ping`
- [ ] `.env` configuré avec `CELERY_BROKER_URL`
- [ ] Test connexion réussi (Python)
- [ ] Celery se connecte : `celery -A config worker`
- [ ] Message "celery@... ready." affiché

---

## 🎉 Félicitations !

Redis est maintenant configuré et prêt à gérer les tâches Celery !

**Prochaine étape** : Testez le système complet !

Consultez **`QUICK_TEST_GUIDE.md`** pour lancer votre premier test. 🚀

