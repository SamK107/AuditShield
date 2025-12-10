# 🌐 Test du Formulaire Web - Étapes Complètes

## ✅ Le Script a Réussi!

**Confirmation:** Le script `test_orange_30_omuv.py` a fonctionné avec 30 OMUV! ✅

**Maintenant:** Vérifier que le formulaire web aboutit au même résultat.

---

## 📋 Étapes à Suivre

### Étape 1: Activer l'Environnement Virtuel

**Commandes Windows (PowerShell):**
```powershell
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield"
..\venv\Scripts\Activate.ps1
```

**OU (si bash/cmd):**
```bash
cd auditshield
..\venv\Scripts\activate
```

---

### Étape 2: Changer le Prix Temporairement

```bash
python change_price_for_test.py
```

**Ce que fait ce script:**
- ✅ Change le prix du produit à **30 FCFA**
- ✅ Sauvegarde le prix original
- ✅ Crée un script `restore_price.py` pour restaurer après

**Résultat attendu:**
```
✅ Prix changé à 30 FCFA!
✅ Script de restauration créé: restore_price.py
```

---

### Étape 3: Lancer le Serveur

```bash
python manage.py runserver
```

**Serveur démarre sur:**
```
http://127.0.0.1:8000/
```

---

### Étape 4: Tester le Paiement

#### 4.1 Ouvrir la Page de Paiement

**Navigateur:**
```
http://127.0.0.1:8000/buy/cinetpay/
```

#### 4.2 Vérifier le Montant

**Sur la page, vous devriez voir:**
```
Montant: 30 FCFA (ou 30 XOF)
```

**Si ce n'est pas le cas, le prix n'a pas été changé!**

#### 4.3 Remplir le Formulaire

**Informations:**
- Email: `test@example.com`
- Prénom: `Test`
- Nom: `User`
- Téléphone: `7701101166`

#### 4.4 Cliquer sur "Payer avec Orange Money ML"

**Bouton orange avec logo Orange Money**

**Résultat attendu:**
- ✅ Redirection vers `https://mpayment.orange-money.com/...`

#### 4.5 Sur Orange Money

**Page affiche:**
```
Montant: 30.00 OMUV
+Frais: 0.00 OMUV
Montant total: 30.00 OMUV
Bénéficiaire: AuditShield
```

**Actions:**
1. Entrer MSISDN: `7701101166`
2. Cliquer "Suivant"
3. Entrer PIN: `4940`
4. Recevoir le code USSD (6 chiffres)
5. Entrer le code
6. Valider

**Résultat attendu:**
```
✅ Paiement réussi!
```

#### 4.6 Retour sur Votre Site

**URL:**
```
http://127.0.0.1:8000/payments/om/return/?order_id=...&status=SUCCESS
```

**Page affiche:**
```
✅ Paiement réussi!
Vous allez recevoir un email.
```

#### 4.7 Vérifier l'Email

**Dans votre boîte email:**
- ✅ Email reçu avec le lien de téléchargement

---

### Étape 5: Restaurer le Prix Normal

**IMPORTANT: Après le test!**

```bash
python restore_price.py
```

**Résultat:**
```
✅ Prix restauré à 15000 FCFA
```

---

## 🔄 Résumé des Commandes

**Commandes complètes (PowerShell):**
```powershell
# 1. Aller dans le dossier
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield"

# 2. Activer venv
..\venv\Scripts\Activate.ps1

# 3. Changer le prix
python change_price_for_test.py

# 4. Lancer le serveur
python manage.py runserver

# ... Tester dans le navigateur ...

# 5. Restaurer le prix (après le test)
python restore_price.py
```

---

## ❓ Questions/Réponses

### Q: Le prix ne change pas sur la page?

**R:** Rafraîchissez la page (`Ctrl+F5`) ou vérifiez:
```bash
python manage.py shell
```
```python
from store.models import Product
p = Product.objects.get(slug='audit-sans-peur')
print(p.price_fcfa)  # Devrait afficher: 30
```

### Q: Le formulaire ne se soumet pas?

**R:** Vérifiez la console navigateur (`F12`) pour les erreurs JavaScript.

### Q: Redirection ne fonctionne pas?

**R:** Vérifiez les logs Django dans le terminal pour voir les erreurs.

### Q: Email non reçu?

**R:** Vérifiez:
- Configuration email dans `settings/dev.py`
- Console Django pour voir si l'email a été envoyé
- Dossier spam

---

## ✅ Résultat Final Attendu

**Si tout fonctionne:**

```
✅ Prix changé à 30 FCFA
✅ Formulaire soumis
✅ Redirection vers Orange Money
✅ Paiement de 30 OMUV réussi (solde: 33 → 3 OMUV)
✅ Retour sur votre site
✅ Email envoyé
✅ Prix restauré à 15000 FCFA

🎉 L'INTÉGRATION EST 100% FONCTIONNELLE VIA LE FORMULAIRE WEB! 🎉
```

---

## 🎯 Conclusion

**OUI, le formulaire web aboutira au même résultat que le script!**

**Pourquoi?**
- Les deux utilisent le même service: `orange_money.create_payment_request()`
- Les deux appellent les mêmes APIs Orange Money
- Les deux avec le même montant: 30 OMUV

**Différence:**
- Le script crée l'Order directement
- Le formulaire crée l'Order via la vue `orange_start_payment()`

**Mais le résultat final est identique!** ✅

---

## 🚀 Actions Immédiates

**1. Changer le prix:**
```bash
cd auditshield
..\venv\Scripts\Activate.ps1
python change_price_for_test.py
```

**2. Lancer le serveur:**
```bash
python manage.py runserver
```

**3. Tester:**
```
http://127.0.0.1:8000/buy/cinetpay/
```

**4. Restaurer:**
```bash
python restore_price.py
```

---

**Lancez ces commandes maintenant et testez le formulaire web!** 🌐✨

**Vous devriez obtenir exactement le même résultat que le script: Paiement réussi! ✅**

