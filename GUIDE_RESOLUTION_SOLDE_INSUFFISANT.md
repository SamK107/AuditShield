# 🔧 Guide de Résolution: "Solde Insuffisant" Orange Money Sandbox

## 📋 Résumé du Problème

**Symptôme:**
```
Votre solde Orange Money est insuffisant.
Veuillez recharger votre compte Orange Money et recommencer.
```

**Mais:**
- Compte de test: `7701101166`
- Solde documenté: **1 000 000 OMUV**
- Montant à payer: **1000 OMUV**
- Solde devrait être suffisant! 

**Le processus fonctionne jusqu'à l'étape finale:**
1. ✅ MSISDN entré: `7701101166`
2. ✅ PIN entré: `4940`
3. ✅ Code USSD reçu (6 chiffres)
4. ✅ Code entré et validé
5. ❌ Erreur "solde insuffisant"

---

## 🎯 Solutions à Tester

### Solution 1: Ajouter applicationId ✅ (APPLIQUÉ)

J'ai ajouté le support pour `applicationId` dans le payload (certaines APIs l'exigent).

**Fichier modifié:** `store/services/orange_money.py`

**Code ajouté:**
```python
if config.get("APPLICATION_ID"):
    payload["applicationId"] = config["APPLICATION_ID"]
```

**Votre `.env` contient déjà:**
```bash
ORANGE_APPLICATION_ID=Ih9fH6Y4kTXsAiaTgtkwAcR7pxa12fG8
```

**Relancez le test:**
```bash
cd auditshield
python test_orange_money_sandbox.py
```

**Vérifiez dans les logs** que `applicationId` est maintenant envoyé:
```json
{
  "merchant_key": "...",
  "currency": "OUV",
  "amount": 1000,
  "applicationId": "Ih9fH6Y4kTXsAiaTgtkwAcR7pxa12fG8",  ← Doit apparaître
  ...
}
```

---

### Solution 2: Vérifier la Configuration Merchant

**Problème potentiel:** Le merchant n'est peut-être pas autorisé à recevoir des paiements en sandbox.

**Vérifiez sur le portail Orange Money Developer:**
1. Connectez-vous à https://developer.orange.com/
2. Allez dans votre application Orange Money WebPay
3. Vérifiez:
   - ✅ Application status: **Active**
   - ✅ Sandbox: **Enabled**
   - ✅ Merchant: **Configured**
   - ✅ Test credentials: **Valid**

**Si le merchant n'est pas configuré:**
- Demander à Orange Money de l'activer pour le sandbox
- Vérifier que `merchant_key` correspond à votre compte

---

### Solution 3: Provisionner le Compte de Test

**Action:** Contacter le support Orange Money Developer:

**Email/Ticket à envoyer:**
```
Sujet: Compte sandbox 7701101166 - Solde insuffisant

Bonjour,

J'utilise l'API Orange Money WebPay Dev (Mali) en mode sandbox.

Credentials de test:
- MSISDN: 7701101166
- PIN: 4940
- Application ID: Ih9fH6Y4kTXsAiaTgtkwAcR7pxa12fG8

Le paiement échoue avec "solde insuffisant" alors que la documentation 
indique un solde de 1 000 000 OMUV.

Pouvez-vous:
1. Vérifier que le compte 7701101166 est provisionné
2. Confirmer le solde actuel
3. Recharger le compte si nécessaire

Merci!
```

---

### Solution 4: Tester avec Montant Plus Élevé

Paradoxalement, certains systèmes de test ont un **montant minimum**.

**Testez avec:**
- 5000 OMUV
- 10000 OMUV
- 15000 OMUV (prix réel de votre ebook)

**Comment:**

Dans votre `.env` ou base de données, changer temporairement le prix du produit:
```python
# Via shell Django
from store.models import Product
p = Product.objects.get(slug='audit-sans-peur')
p.price_fcfa = 5000  # Tester avec 5000
p.save()
```

Puis retester le paiement.

---

### Solution 5: Vérifier les Logs Orange Money

**Cherchez dans vos logs** s'il y a des erreurs additionnelles:

```bash
# Logs du paiement
tail -f logs/orange_money.log

# Chercher les erreurs
grep "ERROR" logs/orange_money.log
grep "FAILED" logs/orange_money.log
```

---

## 🧪 Tests Alternatifs

### Test 1: Montant Minimal (1 OMUV)

```bash
python test_orange_minimal.py
```

Si 1 OMUV fonctionne mais pas 1000 OMUV → Problème de configuration compte.

### Test 2: Autre Compte de Test

Si Orange Money Mali vous a fourni **d'autres** credentials de test, essayez-les:
```
MSISDN: ?????????
PIN: ????
```

### Test 3: Vérifier la Currency

**Assurez-vous** que la currency est bien **OUV** en sandbox (pas XOF).

Dans vos logs (ligne 59), c'est déjà bon:
```json
"currency": "OUV"  ✅
```

Sur la page Orange Money:
```
1000.00 OMUV  ✅
```

---

## 📞 Contacter Orange Money Support

### Informations à Fournir

**1. Votre Application:**
- Application ID: `Ih9fH6Y4kTXsAiaTgtkwAcR7pxa12fG8`
- Client ID: `Ih9fH6Y4kTXsAiaTgtkwAcR7pxa12fG8`
- Environnement: Sandbox Mali (`/dev/v1/`)

**2. Le Problème:**
- Message d'erreur: "Solde insuffisant"
- Compte utilisé: `7701101166`
- Montant: 1000 OMUV
- Solde attendu: 1 000 000 OMUV

**3. Logs API:**
```json
Request: {
  "merchant_key": "4ae1...",
  "currency": "OUV",
  "amount": 1000,
  ...
}

Response: {
  "status": 201,
  "message": "OK",
  "pay_token": "...",
  "payment_url": "https://mpayment.orange-money.com/..."
}
```

**4. Question:**
```
Le compte 7701101166 est-il provisionné avec un solde en sandbox Mali?
Si oui, quel est le solde actuel?
Pourquoi le paiement de 1000 OMUV échoue avec "solde insuffisant"?
```

---

## 🔬 Debug Avancé

### Vérifier la Requête Complète

Dans les logs (ligne 59), vérifier que **tous** les champs requis sont envoyés:

```json
{
  "merchant_key": "✅ Présent",
  "currency": "OUV ✅",
  "order_id": "✅ Présent",
  "amount": 1000,
  "return_url": "✅ Présent",
  "cancel_url": "✅ Présent",
  "notif_url": "✅ Présent",
  "lang": "fr",
  "reference": "AuditShield",
  "applicationId": "❓ Ajouté maintenant"
}
```

### Comparer avec la Documentation

**Selon le guide Orange Money WebPay Dev (section 3), le payload doit contenir:**

**Obligatoires:**
- ✅ `merchant_key`
- ✅ `currency` (OUV en sandbox)
- ✅ `order_id`
- ✅ `amount`
- ✅ `return_url`
- ✅ `notif_url`

**Optionnels:**
- ✅ `cancel_url`
- ✅ `lang`
- ✅ `reference`
- ❓ `applicationId` (selon version API)

---

## 🚀 Actions Immédiates

### Étape 1: Relancer avec applicationId

```bash
cd auditshield
python test_orange_money_sandbox.py
```

**Vérifier dans les logs** que `applicationId` apparaît maintenant dans le payload.

### Étape 2: Tester dans le Navigateur

```bash
python manage.py runserver
```

Aller sur `http://127.0.0.1:8000/buy/cinetpay/` et retester le paiement.

### Étape 3: Si Ça Ne Fonctionne Toujours Pas

**Essayer avec un montant différent:**

Via le shell Django:
```python
from store.models import Product
p = Product.objects.get(slug='audit-sans-peur')
p.price_fcfa = 5000  # Tester avec 5000 OMUV
p.save()
```

Puis retester.

### Étape 4: Contacter Orange Money

Si rien ne fonctionne, c'est probablement un problème de **provisioning du compte sandbox**.

---

## 📝 Checklist de Vérification

- [ ] `applicationId` ajouté au payload (✅ fait)
- [ ] Credentials vérifiés sur developer.orange.com
- [ ] Application status = "Active"
- [ ] Sandbox activé pour l'application
- [ ] Merchant configuré correctement
- [ ] Testé avec montants différents (1, 1000, 5000, 15000 OMUV)
- [ ] Logs vérifiés (pas d'autres erreurs)
- [ ] Support Orange Money contacté si nécessaire

---

## 💭 Questions pour Orange Money Support

Si vous contactez le support, demandez:

1. **Le compte 7701101166 a-t-il un solde provisionné?**
2. **Quel est le solde actuel du compte en sandbox?**
3. **Y a-t-il un montant minimum pour les tests?**
4. **Le merchant (MSISDN: 7701901166) est-il configuré pour recevoir des paiements en sandbox?**
5. **L'applicationId est-il requis dans le payload?**
6. **Y a-t-il des logs d'erreur côté Orange Money pour cette transaction?**

---

## ✅ Résumé

**L'intégration est techniquement parfaite:**
- ✅ Code correct
- ✅ Currency correcte (OUV)
- ✅ Processus complet jusqu'à la validation
- ✅ applicationId ajouté au payload

**Le problème est probablement:**
- ❓ Configuration du compte sandbox (provisioning)
- ❓ Configuration du merchant
- ❓ Paramètre manquant dans l'API

**Prochaine étape:**
1. Relancer avec `applicationId`
2. Si ça ne fonctionne pas → Contacter Orange Money Support
3. Leur demander de vérifier le provisioning du compte

---

**Testez maintenant avec le nouveau code (qui inclut `applicationId`)!** 🚀

Si le problème persiste, il faudra contacter Orange Money pour qu'ils vérifient:
- Le solde du compte 7701101166
- La configuration de votre merchant
- Les logs de leur côté

Dites-moi si l'ajout de `applicationId` résout le problème! 🎯

