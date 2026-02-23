import re

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.medication import Medication


def _clean_ingredient(raw: str) -> str:
    """Clean Cenabast-style ingredient names for pharmacy search.

    Strips numeric prefixes like '1-' or '1.1-', removes dosage info,
    and normalizes whitespace.
    """
    # Remove leading numeric prefix (e.g., "1-aciclovir", "1.1-escitalopram")
    cleaned = re.sub(r"^[\d.]+[-]", "", raw.strip())
    # Remove parenthetical suffixes (e.g., "paracetamol (como sodio)")
    cleaned = re.sub(r"\s*\(.*?\)\s*", " ", cleaned)
    # Remove dosage/form info (anything after %, mg, ml, etc.)
    cleaned = re.sub(r"\s+\d+[\.,]?\d*\s*(%|mg|ml|mcg|ui|g(?!\w)).*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def build_search_queries(db: Session, limit: int = 200) -> list[str]:
    """Build unique search queries from existing medications.

    Uses active_ingredient (deduplicated, cleaned) as primary queries.
    """
    ingredients = db.query(
        func.lower(Medication.active_ingredient)
    ).filter(
        Medication.active_ingredient.isnot(None),
    ).distinct().all()

    queries = set()
    for (ing,) in ingredients:
        if not ing or not ing.strip():
            continue
        cleaned = _clean_ingredient(ing)
        if cleaned and len(cleaned) >= 3:
            queries.add(cleaned)

    result = sorted(queries)
    if limit and len(result) > limit:
        result = result[:limit]

    return result
