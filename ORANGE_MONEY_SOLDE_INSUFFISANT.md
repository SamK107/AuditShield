# 🐛 Orange Money Sandbox: "Solde Insuffisant"

## ❌ Problème

Le paiement échoue avec le message:
```
"Votre solde Orange Money est insuffisant. 
Veuillez recharger votre compte Orange Money et recommencer."
```

**Mais selon la documentation:**
```
Compte de test: 7701101166
PIN: 4940
Solde: 1 000 000 OMUV
Montant à payer: 1000 OMUV
```

Le solde **devrait** être suffisant!

---

## 🔍 Analyse

### Ce Qui Fonctionne ✅

1. ✅ Intégration technique complète
2. ✅ OAuth: Token obtenu (200 OK)
3. ✅ WebPay Init: Payment créé (201 OK)
4. ✅ Redirection: Fonctionne
5. ✅ Page Orange Money: S'affiche
6. ✅ MSISDN + PIN: Acceptés
7. ✅ Code USSD: Généré et envoyé
8. ✅ Code entré: Validé

### Ce Qui Échoue ❌

9. ❌ Validation finale du paiement → "Solde insuffisant"

---

## 💡 Causes Possibles

### Cause 1: Compte Non Provisionné

Le compte `7701101166` n'est peut-être **pas réellement provisionné** avec 1 million OMUV dans votre environnement sandbox.

**Solution:**
- Contacter Orange Money Developer Support
- Demander: "Le compte 7701101166 est-il provisionné avec un solde en sandbox Mali?"
- Demander de provisionner le compte si nécessaire

### Cause 2: Merchant Non Configuré

Votre merchant (bénéficiaire) n'est peut-être pas correctement configuré pour recevoir des paiements en sandbox.

**Vérifiez:**
```bash
ORANGE_MERCHANT_MSISDN=7701901166  # Doit correspondre à votre compte merchant
ORANGE_MERCHANT_AGENT_CODE=102786  # Doit être valide
ORANGE_MERCHANT_KEY=4ae1...        # Doit être correct
```

**Action:**
- Vérifier ces valeurs avec Orange Money
- S'assurer que le merchant est activé pour le sandbox

### Cause 3: Montant Minimum

Certains sandboxes ont un montant minimum (ex: 5000 OMUV).

**Test:**
- Essayer avec 5000 OMUV
- Essayer avec 10000 OMUV
- Voir si le paiement passe

### Cause 4: Configuration API

L'API `/dev/v1/webpayment` pourrait nécessiter des paramètres supplémentaires.

**Vérifiez dans les logs API (ligne 59):**
```json
{
  "merchant_key": "4ae1***",
  "currency": "OUV",
  "order_id": "...",
  "amount": 1000,
  "return_url": "...",
  "cancel_url": "...",
  "notif_url": "...",
  "lang": "fr",
  "reference": "AuditShield"
}
```

**Manque-t-il quelque chose?** Certaines APIs Orange Money demandent:
- `applicationId` (ORANGE_APPLICATION_ID)
- `merchant_msisdn`
- `agent_code`

---

## 🔧 Solutions à Tester

### Solution A: Ajouter applicationId au Payload

L'API WebPay Dev pourrait nécessiter `applicationId`:

<function_calls>
<invoke name="search_replace">
<parameter name="file_path">auditshield/store/services/orange_money.py
