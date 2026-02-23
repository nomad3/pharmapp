import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to URL-safe slug. Handles Spanish characters."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def medication_slug(name: str, dosage: str | None = None, lab: str | None = None) -> str:
    parts = [name]
    if dosage and dosage.lower() not in name.lower():
        parts.append(dosage)
    if lab:
        parts.append(lab)
    return slugify(" ".join(parts))
