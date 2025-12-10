# 🌐 Tester le Paiement Orange Money via le Formulaire Web

## 🎯 Objectif

Vérifier que le formulaire web (`http://127.0.0.1:8000/buy/cinetpay/`) aboutit au même résultat que le script de test (paiement réussi avec 30 OMUV).

---

## ⚙️ Étape 1: Changer le Prix Temporairement

**Pour que le test fonctionne, le produit doit coûter 30 FCFA (solde disponible: 33 OMUV).**

### Lancer le Script

```bash
cd auditshield
python change_price_for_test.py
```

**Résultat attendu:**
```
================================================================================
 CHANGEMENT DE PRIX TEMPORAIRE POUR TEST
================================================================================

Produit: Audit Sans Peur
Prix actuel: 15000 FCFA
Nouveau prix: 30 FCFA (pour test avec solde de 33 OMUV)

✅ Prix changé à 30 FCFA!

🧪 Testez maintenant:
  1. python manage.py runserver
  2. Ouvrir: http://127.0.0.1:8000/buy/cinetpay/
  3. Remplir le formulaire
  4. Cliquer sur 'Payer avec Orange Money ML'
  5. Finaliser le paiement avec MSISDN: 7701101166 et PIN: 4940
  6. Le paiement devrait RÉUSSIR! ✅

⚠️  IMPORTANT: Remettre le prix normal après le test:
  python restore_price.py

✅ Script de restauration créé: restore_price.py
```

---

## 🌐 Étape 2: Lancer le Serveur Django

```bash
python manage.py runserver
```

---

## 🧪 Étape 3: Tester le Paiement

### 3.1 Ouvrir la Page de Paiement

```
http://127.0.0.1:8000/buy/cinetpay/
```

### 3.2 Remplir le Formulaire

**Champs à remplir:**
- **Email:** test@example.com (ou votre email)
- **Prénom:** Test
- **Nom:** User
- **Téléphone:** 7701101166 (ou autre)

**Vérifier:**
- ✅ Le montant affiché devrait être: **30 FCFA** (ou 30 XOF)

### 3.3 Cliquer sur "Payer avec Orange Money ML"

**Bouton:** Orange Money (avec le logo Orange)

**Action attendue:**
- ✅ Redirection vers `https://mpayment.orange-money.com/...`
- ✅ Page de paiement Orange Money s'affiche

### 3.4 Sur la Page Orange Money

**Informations affichées:**
```
Montant: 30.00 OMUV
+Frais: 0.00 OMUV
Montant total: 30.00 OMUV
Bénéficiaire: AuditShield
```

**Étapes:**
1. **Entrer le MSISDN:** `7701101166`
2. **Cliquer sur "Suivant"**
3. **Entrer le PIN:** `4940`
4. **Recevoir le code USSD** (6 chiffres)
5. **Entrer le code USSD**
6. **Valider**

**Résultat attendu:**
```
✅ Paiement réussi!
Votre paiement de 30.00 OMUV a été effectué avec succès.
```

### 3.5 Redirection vers Votre Site

**URL de retour:**
```
http://127.0.0.1:8000/payments/om/return/?order_id=...&status=SUCCESS
```

**Page affichée:**
```
✅ Paiement réussi!
Merci pour votre achat.
Vous allez recevoir un email avec le lien de téléchargement.
```

---

## 📧 Étape 4: Vérifier l'Email

**Si le paiement réussit, un email devrait être envoyé:**

**Sujet:** `Votre ebook Audit Sans Peur`

**Corps:**
```
Bonjour Test,

Merci pour votre achat!

Voici le lien de téléchargement de votre ebook:
http://127.0.0.1:8000/download/...

Ce lien est valable pendant 30 jours.

Cordialement,
L'équipe AuditShield
```

**Vérifier:**
- ✅ Email reçu
- ✅ Lien de téléchargement fonctionnel

---

## 🔄 Étape 5: Restaurer le Prix Normal

**IMPORTANT: Après le test, remettre le prix original!**

```bash
python restore_price.py
```

**Résultat attendu:**
```
✅ Prix restauré à 15000 FCFA
```

---

## 📊 Comparaison: Script vs Formulaire

| Étape | Script (`test_orange_30_omuv.py`) | Formulaire Web | Status |
|-------|-----------------------------------|----------------|--------|
| Montant | 30 OMUV | 30 OMUV (après changement prix) | ✅ |
| API Call | ✅ create_payment_request() | ✅ orange_start_payment() | ✅ |
| OAuth Token | ✅ Obtenu | ✅ Obtenu | ✅ |
| WebPay Init | ✅ 201 OK | ✅ 201 OK | ✅ |
| Payment URL | ✅ Générée | ✅ Générée | ✅ |
| Redirection | ✅ Manuelle | ✅ Automatique | ✅ |
| Paiement | ✅ Réussi | ✅ Devrait réussir | 🧪 |
| Webhook | ❓ Pas testé | ✅ Appelé (si configuré) | 🧪 |
| Email | ❓ Pas envoyé | ✅ Envoyé | 🧪 |

**Conclusion:**
- Le script teste l'API directement ✅
- Le formulaire teste le flux complet ✅
- Les deux devraient aboutir au même résultat! ✅

---

## 🔍 Debug: Si le Formulaire Ne Fonctionne Pas

### Vérifier les Logs

**Terminal Django:**
```
[start_checkout] Request method: POST
[start_checkout] Product slug: audit-sans-peur
[start_checkout] Provider key: orange_money_ml
[start_checkout] POST data: {...}
[OM][create_payment] Order ID: ...
[OM][oauth] Token obtenu avec succès
[OM][create_payment] WebPayment initialisé | pay_token=...
```

### Vérifier le Prix

**Si le montant n'est pas 30 OMUV:**
```bash
python manage.py shell
```

```python
from store.models import Product
p = Product.objects.get(slug='audit-sans-peur')
print(p.price_fcfa)  # Devrait afficher: 30
```

### Vérifier le Provider

**Dans `buy_cinetpay.html`, le bouton doit avoir:**
```html
<button ... value="orange_money_ml" ...>
  Payer avec Orange Money ML
</button>
```

**Pas `value="orange"`!**

---

## ✅ Checklist Complète

### Avant le Test
- [ ] Lancer `python change_price_for_test.py`
- [ ] Vérifier que le prix est changé à 30 FCFA
- [ ] Lancer `python manage.py runserver`

### Pendant le Test
- [ ] Ouvrir `http://127.0.0.1:8000/buy/cinetpay/`
- [ ] Vérifier que le montant affiché est 30 FCFA
- [ ] Remplir le formulaire
- [ ] Cliquer sur "Payer avec Orange Money ML"
- [ ] Redirection vers Orange Money ✅
- [ ] Entrer MSISDN: 7701101166
- [ ] Entrer PIN: 4940
- [ ] Entrer le code USSD reçu
- [ ] Paiement réussi ✅
- [ ] Redirection vers votre site ✅
- [ ] Email reçu ✅

### Après le Test
- [ ] Lancer `python restore_price.py`
- [ ] Vérifier que le prix est restauré à 15000 FCFA

---

## 🎊 Résultat Final Attendu

**Si tout fonctionne:**
```
✅ Prix changé à 30 FCFA
✅ Formulaire rempli
✅ Bouton "Payer avec Orange Money ML" cliqué
✅ Redirection vers Orange Money
✅ Paiement de 30 OMUV réussi
✅ Redirection vers votre site
✅ Email envoyé avec lien de téléchargement
✅ Prix restauré à 15000 FCFA

🎉 L'INTÉGRATION ORANGE MONEY EST 100% FONCTIONNELLE! 🎉
```

---

## 🚀 Prochaines Étapes

Une fois le test réussi:

1. **Demander à Orange Money de recharger le compte:**
   - Email au support pour recharger `7701101166` à 1M OMUV

2. **Tester avec le prix réel:**
   - Une fois le compte rechargé, tester avec 15000 FCFA

3. **Configurer le Webhook pour la production:**
   - Utiliser ngrok ou un vrai domaine
   - Tester que les notifications fonctionnent

4. **Passer en production:**
   - Changer les URLs sandbox → production
   - Utiliser les vrais credentials
   - Mettre à jour les URL de retour/notification

---

**Lancez maintenant `python change_price_for_test.py` et testez via le formulaire web!** 🌐🎯

