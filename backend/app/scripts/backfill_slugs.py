"""
Backfill slugs for all medications that don't have one yet.

Usage:
    python -m app.scripts.backfill_slugs
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.medication import Medication
from app.utils.slugify import medication_slug

BATCH_SIZE = 500


def backfill_slugs():
    db: Session = SessionLocal()
    try:
        medications = (
            db.query(Medication)
            .filter(Medication.slug.is_(None))
            .all()
        )
        print(f"Found {len(medications)} medications without slugs")

        seen_slugs: set[str] = set()

        # Collect existing slugs to avoid duplicates
        existing = (
            db.query(Medication.slug)
            .filter(Medication.slug.isnot(None))
            .all()
        )
        for (s,) in existing:
            seen_slugs.add(s)

        updated = 0
        for med in medications:
            slug = medication_slug(med.name, med.dosage, med.lab)

            # Handle duplicates by appending first 6 chars of UUID
            if slug in seen_slugs:
                slug = f"{slug}-{str(med.id)[:6]}"

            # Safety check: if still duplicate, use full short UUID
            if slug in seen_slugs:
                slug = f"{slug}-{str(med.id)[:12]}"

            seen_slugs.add(slug)
            med.slug = slug
            updated += 1

            if updated % BATCH_SIZE == 0:
                db.commit()
                print(f"  Committed {updated} slugs...")

        db.commit()
        print(f"Done. Updated {updated} medications with slugs.")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_slugs()
