# 🚀 Quick Start - Test Orange Money

## ✅ Statut : TOUT EST PRÊT !

Le flux Orange Money est **100% opérationnel**. Voici comment tester rapidement.

---

## 🎯 Test Rapide (5 minutes)

### 1. Démarrer le serveur
```bash
cd auditshield
python manage.py runserver
```

### 2. Accéder à la page de checkout
```
http://127.0.0.1:8000/buy/cinetpay-orange/?provider=orange_money_ml
```

### 3. Remplir et soumettre
```
Nom : Test
Prénom : Orange
Email : test@example.com
Téléphone : +22370123456
Provider : Orange Money Mali (sélectionné)
```

Cliquer sur **"Payer avec Orange Money Mali"**

### 4. Dans WebPay Sandbox
- Valider le paiement

### 5. Vérifier la page de succès
Vous devriez voir :
- ✅ Bannière verte "Paiement confirmé 🎉"
- ✅ Bouton "Accéder à la page de téléchargement"
- ✅ Bouton "Voir les ressources bonus"
- ✅ Bouton "M'envoyer à nouveau les liens"

### 6. Tester les liens
Cliquer sur chaque bouton pour vérifier qu'ils fonctionnent.

---

## 📋 URLs Importantes

### Checkout
```
http://127.0.0.1:8000/buy/cinetpay-orange/
http://127.0.0.1:8000/buy/cinetpay-orange/?provider=orange_money_ml
```

### Callbacks Orange Money (automatiques)
```
Return:  http://127.0.0.1:8000/payments/om/return/
Cancel:  http://127.0.0.1:8000/payments/om/cancel/
Notify:  http://127.0.0.1:8000/payments/om/notify/
```

### Téléchargements (après paiement)
```
Ebook:     /downloads/secure/<UUID>/
Bonus:     /downloads/resources/<UUID>/
Renvoyer:  /downloads/resend-links/
```

---

## 🧪 Test du Webhook (optionnel)

```bash
# Simuler un webhook Orange Money
curl -X POST http://127.0.0.1:8000/payments/om/notify/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER-xxx",
    "status": "SUCCESS",
    "pay_token": "TXN-123"
  }'
```

Remplacer `ORDER-xxx` par un vrai `provider_ref` de votre base.

---

## 📁 Fichiers Créés / Modifiés

### Nouveaux fichiers ✨
- `store/utils/downloads.py` - Helper pour construire les URLs
- `GUIDE_TEST_ORANGE_MONEY.md` - Guide complet de test
- `ORANGE_MONEY_IMPLEMENTATION_COMPLETE.md` - Documentation complète
- `QUICK_START_ORANGE_MONEY.md` - Ce fichier

### Fichiers existants (déjà en place) ✅
- `store/payment_views.py` - Vues `orange_return`, `orange_cancel`, `orange_notify`
- `store/urls.py` - Routes `/payments/om/*`
- `store/templates/store/payments/` - Tous les templates HTML

---

## 🎬 Enregistrer la Démo Vidéo

### Script court (2 minutes)

1. **Intro** (5 sec)
   > "Voici l'intégration Orange Money sur AuditShield"

2. **Checkout** (20 sec)
   - Montrer la page avec bandeau Orange Money
   - Remplir le formulaire
   - Cliquer sur "Payer avec Orange Money Mali"

3. **WebPay** (10 sec)
   - Montrer l'interface Orange Money
   - Valider le paiement

4. **Succès** (45 sec) ⭐
   - Montrer la page de succès professionnelle
   - Cliquer sur "Accéder à la page de téléchargement"
   - Montrer les 2 formats PDF
   - Revenir et cliquer sur "Voir les ressources bonus"
   - Montrer les ressources

5. **Annulation** (20 sec)
   - Refaire un paiement
   - Annuler dans WebPay
   - Montrer la page d'annulation

6. **Conclusion** (5 sec)
   > "Le flux est complet et prêt pour la production"

---

## ✅ Checklist Rapide

Avant de dire "C'est bon" :

- [ ] J'ai testé un paiement réussi
- [ ] Les 3 boutons de la page de succès fonctionnent
- [ ] J'ai testé une annulation
- [ ] Le design est cohérent et professionnel
- [ ] Aucune erreur dans les logs
- [ ] Le flux CinetPay fonctionne toujours

---

## 🆘 Problème ?

### Le paiement ne passe pas en PAID
**Solution** : Le webhook n'a peut-être pas été traité. Vérifier les logs `[OM][notify]`.

### Les liens de téléchargement ne fonctionnent pas
**Solution** : Vérifier que la session contient `order_email` et `paid_orders`.

### Page blanche ou erreur 500
**Solution** : Vérifier les logs Django pour voir l'erreur exacte.

---

## 🎉 C'est Tout !

Si ces 3 scénarios fonctionnent, **vous êtes prêt** :
1. ✅ Paiement réussi → Page de succès avec liens
2. ✅ Paiement annulé → Page d'annulation propre
3. ✅ Liens de téléchargement fonctionnels

**Prochaine étape** : Enregistrer la vidéo et soumettre à Orange Money ! 🚀

---

**Besoin de plus de détails ?** → Voir `GUIDE_TEST_ORANGE_MONEY.md`  
**Documentation complète ?** → Voir `ORANGE_MONEY_IMPLEMENTATION_COMPLETE.md`
