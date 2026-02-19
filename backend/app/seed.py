"""Seed the database with sample Chilean pharmacy and medication data."""
from app.core.database import SessionLocal
from app.models import Base
from app.core.database import engine
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
from geoalchemy2.elements import WKTElement
import random

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Medication).count() > 0:
        print("Database already seeded")
        db.close()
        return

    meds = [
        Medication(name="Paracetamol 500mg", active_ingredient="Paracetamol", dosage="500mg", form="comprimido", lab="Chile Lab", requires_prescription=False),
        Medication(name="Ibuprofeno 400mg", active_ingredient="Ibuprofeno", dosage="400mg", form="comprimido", lab="Saval", requires_prescription=False),
        Medication(name="Amoxicilina 500mg", active_ingredient="Amoxicilina", dosage="500mg", form="cápsula", lab="Bagó", requires_prescription=True),
        Medication(name="Losartán 50mg", active_ingredient="Losartán", dosage="50mg", form="comprimido", lab="Andrómaco", requires_prescription=True),
        Medication(name="Omeprazol 20mg", active_ingredient="Omeprazol", dosage="20mg", form="cápsula", lab="Mintlab", requires_prescription=False),
    ]
    db.add_all(meds)
    db.flush()

    pharmacies = [
        Pharmacy(chain="cruz_verde", name="Cruz Verde Providencia", address="Av. Providencia 1234", comuna="Providencia", location=WKTElement("POINT(-70.6109 -33.4264)", srid=4326), phone="+56222345678"),
        Pharmacy(chain="salcobrand", name="Salcobrand Las Condes", address="Av. Apoquindo 4500", comuna="Las Condes", location=WKTElement("POINT(-70.5790 -33.4103)", srid=4326), phone="+56223456789"),
        Pharmacy(chain="ahumada", name="Farmacias Ahumada Centro", address="Paseo Ahumada 312", comuna="Santiago", location=WKTElement("POINT(-70.6506 -33.4378)", srid=4326), phone="+56224567890"),
        Pharmacy(chain="dr_simi", name="Dr. Simi Maipú", address="Av. Pajaritos 2100", comuna="Maipú", location=WKTElement("POINT(-70.7574 -33.5100)", srid=4326), phone="+56225678901"),
    ]
    db.add_all(pharmacies)
    db.flush()

    for med in meds:
        for pharm in pharmacies:
            db.add(Price(
                medication_id=med.id,
                pharmacy_id=pharm.id,
                price=round(random.uniform(800, 15000), 0),
                in_stock=random.choice([True, True, True, False]),
            ))

    db.commit()
    db.close()
    print("Seeded database with sample data")

if __name__ == "__main__":
    seed()
