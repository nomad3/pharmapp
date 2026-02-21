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
        # BMS Oncology / Hematology drugs
        Medication(name="Nivolumab 40mg", active_ingredient="Nivolumab", dosage="40mg", form="inyectable", lab="BMS", requires_prescription=True),
        Medication(name="Nivolumab 100mg", active_ingredient="Nivolumab", dosage="100mg", form="inyectable", lab="BMS", requires_prescription=True),
        Medication(name="Nivolumab 240mg", active_ingredient="Nivolumab", dosage="240mg", form="inyectable", lab="BMS", requires_prescription=True),
        Medication(name="Pembrolizumab 100mg", active_ingredient="Pembrolizumab", dosage="100mg", form="inyectable", lab="MSD", requires_prescription=True),
        Medication(name="Ipilimumab 50mg", active_ingredient="Ipilimumab", dosage="50mg", form="inyectable", lab="BMS", requires_prescription=True),
        Medication(name="Atezolizumab 1200mg", active_ingredient="Atezolizumab", dosage="1200mg", form="inyectable", lab="Roche", requires_prescription=True),
        Medication(name="Durvalumab 500mg", active_ingredient="Durvalumab", dosage="500mg", form="inyectable", lab="AstraZeneca", requires_prescription=True),
        Medication(name="Avelumab 200mg", active_ingredient="Avelumab", dosage="200mg", form="inyectable", lab="Merck/Pfizer", requires_prescription=True),
        Medication(name="Dasatinib 50mg", active_ingredient="Dasatinib", dosage="50mg", form="comprimido", lab="BMS", requires_prescription=True),
        Medication(name="Dasatinib 70mg", active_ingredient="Dasatinib", dosage="70mg", form="comprimido", lab="BMS", requires_prescription=True),
        Medication(name="Dasatinib 100mg", active_ingredient="Dasatinib", dosage="100mg", form="comprimido", lab="BMS", requires_prescription=True),
        Medication(name="Imatinib 400mg", active_ingredient="Imatinib", dosage="400mg", form="comprimido", lab="Novartis", requires_prescription=True),
        Medication(name="Nilotinib 200mg", active_ingredient="Nilotinib", dosage="200mg", form="cápsula", lab="Novartis", requires_prescription=True),
        Medication(name="Ponatinib 45mg", active_ingredient="Ponatinib", dosage="45mg", form="comprimido", lab="Takeda", requires_prescription=True),
        Medication(name="Bosutinib 500mg", active_ingredient="Bosutinib", dosage="500mg", form="comprimido", lab="Pfizer", requires_prescription=True),
        Medication(name="Lenalidomida 25mg", active_ingredient="Lenalidomida", dosage="25mg", form="cápsula", lab="BMS/Celgene", requires_prescription=True),
        Medication(name="Lenalidomida 10mg", active_ingredient="Lenalidomida", dosage="10mg", form="cápsula", lab="BMS/Celgene", requires_prescription=True),
        Medication(name="Pomalidomida 4mg", active_ingredient="Pomalidomida", dosage="4mg", form="cápsula", lab="BMS/Celgene", requires_prescription=True),
        Medication(name="Talidomida 100mg", active_ingredient="Talidomida", dosage="100mg", form="cápsula", lab="Varios", requires_prescription=True),
        Medication(name="Bortezomib 3.5mg", active_ingredient="Bortezomib", dosage="3.5mg", form="inyectable", lab="Janssen", requires_prescription=True),
        Medication(name="Carfilzomib 60mg", active_ingredient="Carfilzomib", dosage="60mg", form="inyectable", lab="Amgen", requires_prescription=True),
        Medication(name="Daratumumab 400mg", active_ingredient="Daratumumab", dosage="400mg", form="inyectable", lab="Janssen", requires_prescription=True),
        Medication(name="Elotuzumab 400mg", active_ingredient="Elotuzumab", dosage="400mg", form="inyectable", lab="BMS", requires_prescription=True),
        Medication(name="Rituximab 500mg", active_ingredient="Rituximab", dosage="500mg", form="inyectable", lab="Roche", requires_prescription=True),
        Medication(name="Ibrutinib 140mg", active_ingredient="Ibrutinib", dosage="140mg", form="cápsula", lab="Janssen", requires_prescription=True),
        Medication(name="Venetoclax 100mg", active_ingredient="Venetoclax", dosage="100mg", form="comprimido", lab="AbbVie", requires_prescription=True),
        Medication(name="Ruxolitinib 20mg", active_ingredient="Ruxolitinib", dosage="20mg", form="comprimido", lab="Novartis", requires_prescription=True),
        Medication(name="Azacitidina 100mg", active_ingredient="Azacitidina", dosage="100mg", form="inyectable", lab="BMS/Celgene", requires_prescription=True),
        Medication(name="Decitabina 50mg", active_ingredient="Decitabina", dosage="50mg", form="inyectable", lab="Janssen", requires_prescription=True),
        Medication(name="Cabozantinib 60mg", active_ingredient="Cabozantinib", dosage="60mg", form="comprimido", lab="Ipsen", requires_prescription=True),
        Medication(name="Sunitinib 50mg", active_ingredient="Sunitinib", dosage="50mg", form="cápsula", lab="Pfizer", requires_prescription=True),
        Medication(name="Pazopanib 400mg", active_ingredient="Pazopanib", dosage="400mg", form="comprimido", lab="Novartis", requires_prescription=True),
        Medication(name="Axitinib 5mg", active_ingredient="Axitinib", dosage="5mg", form="comprimido", lab="Pfizer", requires_prescription=True),
        Medication(name="Sorafenib 200mg", active_ingredient="Sorafenib", dosage="200mg", form="comprimido", lab="Bayer", requires_prescription=True),
        Medication(name="Everolimus 10mg", active_ingredient="Everolimus", dosage="10mg", form="comprimido", lab="Novartis", requires_prescription=True),
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
