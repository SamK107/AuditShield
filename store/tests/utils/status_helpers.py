def coerce_status(model_cls, name_fallback: str):
    """
    Renvoie la valeur correcte du statut 'name_fallback' pour model_cls,
    en privilégiant model_cls.Status.<NAME> s'il existe,
    sinon en mappant depuis .choices (minuscule, etc.).
    """
    # 1) TextChoices ?
    Status = getattr(model_cls, "Status", None)
    if Status and hasattr(Status, name_fallback):
        return getattr(Status, name_fallback)

    # 2) Sinon chercher dans le Field.choices
    # Détecte le champ de statut (status/state)
    status_field_name = None
    for field in model_cls._meta.fields:
        if hasattr(field, "choices") and field.choices:
            if field.name.lower() in ("status", "state"):
                status_field_name = field.name
                break
    if not status_field_name:
        status_field_name = "status"  # fallback
    field = model_cls._meta.get_field(status_field_name)
    lower = name_fallback.lower()
    for value, _label in field.choices or []:
        if str(value).lower() == lower:
            return value

    # 3) Fallback brut (mieux vaut échouer explicitement si pas trouvé)
    return lower
