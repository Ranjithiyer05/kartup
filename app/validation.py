import unicodedata

from .models import NAME_MAX_LENGTH

LABELS = {"name": "Name", "surname": "Surname"}


def clean_field(value):
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFC", value)
    return " ".join(value.split())


def validate_submission(payload):
    """Return (cleaned_data, errors). errors maps field -> friendly message."""
    data, errors = {}, {}
    payload = payload if isinstance(payload, dict) else {}
    for field, label in LABELS.items():
        value = clean_field(payload.get(field))
        if not value:
            errors[field] = f"Please enter your {label.lower()}."
        elif len(value) > NAME_MAX_LENGTH:
            errors[field] = f"{label} must be {NAME_MAX_LENGTH} characters or fewer."
        data[field] = value
    return data, errors
