# Debug signature HMAC CinetPay – Django tests

## Problème

Les tests Django pour le webhook CinetPay échouent systématiquement sur la vérification de la signature HMAC (HTTP 400), même lorsque les helpers de test sont corrigés pour générer la signature comme en production.

## Contexte
- La vue Django vérifie la signature HMAC-SHA256 sur le body brut du webhook, accepte hex / sha256=<hex> / base64.
- Les tests génèrent le payload avec toutes les clés attendues (`transaction_id`, `cpm_trans_id`, `order_id`), signent sur les raw bytes, injectent le header et le secret dans l'env.
- Malgré tout, tous les tests qui attendent 200 reçoivent 400 (signature invalide).

## Hypothèse
- Il y a un décalage entre le secret ou le header utilisé côté test et côté vue, ou le body n'est pas identique à celui signé.

## Action : Ajouter des logs détaillés dans la vue

Dans la vue `cinetpay_callback`, juste avant la validation de la signature, ajoute :

```python
import logging
import os
import binascii

# ... dans la vue cinetpay_callback ...
header_name = get_webhook_header()
sig = request.headers.get(header_name) or request.META.get(f"HTTP_{header_name.upper().replace('-','_')}")
raw = request.body or b""

# Ajout de logs détaillés pour debug
logger = logging.getLogger(__name__)
logger.warning(
    "[DEBUG CinetPay] header_name=%r sig=%r env_secret=%r body_len=%d body_sha256=%s",
    header_name,
    sig,
    os.getenv("CINETPAY_WEBHOOK_SECRET"),
    len(raw),
    binascii.hexlify(__import__('hashlib').sha256(raw).digest()).decode()
)
# Optionnel : log le body lui-même (attention à la taille/sensibilité)
logger.warning("[DEBUG CinetPay] body=%r", raw)
```

À placer juste avant :

```python
if not sig or not verify_signature(sig, raw):
    logger.warning(
        "Invalid signature: header=%s body_len=%d body_sha256=%s",
        header_name, len(raw), _hl.sha256(raw).hexdigest()
    )
    return HttpResponseBadRequest("Invalid signature")
```

## Ce que ça va afficher dans les logs :
- Le nom du header utilisé
- La valeur de la signature reçue
- Le secret utilisé côté vue (doit être "testsecret")
- La longueur du body reçu
- Le SHA256 du body reçu (pour vérifier qu'il est identique à celui signé côté test)
- (Optionnel) Le body lui-même

## But
Comparer ces valeurs à celles générées côté test pour voir où se situe la divergence (secret, header, body, encodage…).

## Prompt à donner à un collègue

```
On a corrigé tous les helpers de tests pour utiliser .hexdigest(), le payload contient bien toutes les clés, le header et le secret sont bien injectés dans l'env, la signature est calculée sur les raw bytes postés. Pourtant, tous les tests qui attendent 200 reçoivent 400.

Pour diagnostiquer, ajoute ces logs juste avant la validation de la signature dans la vue :

import logging
import os
import binascii

# ... dans la vue cinetpay_callback ...
header_name = get_webhook_header()
sig = request.headers.get(header_name) or request.META.get(f"HTTP_{header_name.upper().replace('-','_')}")
raw = request.body or b""

logger = logging.getLogger(__name__)
logger.warning(
    "[DEBUG CinetPay] header_name=%r sig=%r env_secret=%r body_len=%d body_sha256=%s",
    header_name,
    sig,
    os.getenv("CINETPAY_WEBHOOK_SECRET"),
    len(raw),
    binascii.hexlify(__import__('hashlib').sha256(raw).digest()).decode()
)
logger.warning("[DEBUG CinetPay] body=%r", raw)

# ... puis la validation signature comme avant ...

Compare les valeurs loguées à celles générées côté test pour trouver la divergence (secret, header, body, encodage…).
```
