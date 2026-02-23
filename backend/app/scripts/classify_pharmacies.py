"""
Classify pharmacies as retail or non-retail.

Retail pharmacies are consumer-facing stores where individuals can buy medicines.
Non-retail entities include hospitals, clinics, foundations, municipal health centers,
and other institutional buyers that appear in Cenabast data but are not pharmacies.

Usage:
    python -m app.scripts.classify_pharmacies
"""

from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.pharmacy import Pharmacy

# Known retail pharmacy chains (scraped sources) — always retail
RETAIL_CHAINS = {"cruz_verde", "salcobrand", "ahumada", "dr_simi"}

# Patterns in pharmacy name that indicate non-retail institutional entities
NON_RETAIL_PATTERNS = [
    "ASOC",
    "FUNDACION",
    "CORPORACION",
    "HOSPITAL",
    "CLINICA",
    "CESFAM",
    "CONSULTORIO",
    "MUNICIPALI",
    "SERVICIO DE SALUD",
    "INSTITUTO",
    "HOGAR",
    "CENTRO DE SALUD",
]


def classify_pharmacies():
    db = SessionLocal()
    try:
        total = db.query(func.count(Pharmacy.id)).scalar()
        print(f"Total pharmacies: {total}")

        # 1. Known retail chains — mark as retail
        retail_chain_count = (
            db.query(Pharmacy)
            .filter(Pharmacy.chain.in_(RETAIL_CHAINS))
            .update({Pharmacy.is_retail: True}, synchronize_session=False)
        )
        print(f"Retail chains (cruz_verde, salcobrand, ahumada, dr_simi): {retail_chain_count}")

        # 2. Cenabast pharmacies with "FARMACIA" in name — retail
        farmacia_count = (
            db.query(Pharmacy)
            .filter(
                Pharmacy.chain == "cenabast",
                func.upper(Pharmacy.name).contains("FARMACIA"),
            )
            .update({Pharmacy.is_retail: True}, synchronize_session=False)
        )
        print(f"Cenabast with 'FARMACIA' in name: {farmacia_count}")

        # 3. Cenabast pharmacies matching blocklist patterns — NOT retail
        non_retail_count = 0
        for pattern in NON_RETAIL_PATTERNS:
            count = (
                db.query(Pharmacy)
                .filter(
                    Pharmacy.chain == "cenabast",
                    func.upper(Pharmacy.name).contains(pattern),
                )
                .update({Pharmacy.is_retail: False}, synchronize_session=False)
            )
            if count > 0:
                print(f"  Non-retail pattern '{pattern}': {count}")
            non_retail_count += count

        print(f"Cenabast non-retail (blocklist matches): {non_retail_count}")

        # 4. Remaining cenabast entries without "FARMACIA" and not in blocklist —
        #    keep as retail (conservative default; server_default is true)
        remaining = (
            db.query(func.count(Pharmacy.id))
            .filter(
                Pharmacy.chain == "cenabast",
                Pharmacy.is_retail == True,
                ~func.upper(Pharmacy.name).contains("FARMACIA"),
            )
            .scalar()
        )
        print(f"Cenabast remaining (kept as retail): {remaining}")

        db.commit()

        # Summary
        final_retail = db.query(func.count(Pharmacy.id)).filter(Pharmacy.is_retail == True).scalar()
        final_non_retail = db.query(func.count(Pharmacy.id)).filter(Pharmacy.is_retail == False).scalar()
        print(f"\n--- Summary ---")
        print(f"Retail:     {final_retail}")
        print(f"Non-retail: {final_non_retail}")
        print(f"Total:      {final_retail + final_non_retail}")

    finally:
        db.close()


if __name__ == "__main__":
    classify_pharmacies()
