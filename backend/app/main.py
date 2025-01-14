from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Medicamento(BaseModel):
    id: int
    nombre: str
    descripcion: str

# Datos de ejemplo
medicamentos = [
    {"id": 1, "nombre": "Paracetamol", "descripcion": "Alivia el dolor y reduce la fiebre."},
    {"id": 2, "nombre": "Ibuprofeno", "descripcion": "Antiinflamatorio y analgésico."},
    {"id": 3, "nombre": "Amoxicilina", "descripcion": "Antibiótico para infecciones bacterianas."},
]

@app.get("/medicamentos", response_model=List[Medicamento])
def obtener_medicamentos():
    return medicamentos

class Farmacia(BaseModel):
    id: int
    nombre: str
    direccion: str
    latitud: float
    longitud: float

farmacias = [
    {"id": 1, "nombre": "Farmacia Central", "direccion": "Calle Falsa 123", "latitud": 40.4168, "longitud": -3.7038},
    {"id": 2, "nombre": "Farmacia Salud", "direccion": "Avenida Siempre Viva 456", "latitud": 40.4178, "longitud": -3.7048},
    {"id": 3, "nombre": "Farmacia Bienestar", "direccion": "Plaza Mayor 789", "latitud": 40.4188, "longitud": -3.7058},
]

@app.get("/farmacias", response_model=List[Farmacia])
def obtener_farmacias():
    return farmacias

class Precio(BaseModel):
    medicamento_id: int
    farmacia_id: int
    precio: float

precios = [
    {"medicamento_id": 1, "farmacia_id": 1, "precio": 5.50},
    {"medicamento_id": 1, "farmacia_id": 2, "precio": 5.00},
    {"medicamento_id": 1, "farmacia_id": 3, "precio": 5.75},
    {"medicamento_id": 2, "farmacia_id": 1, "precio": 7.20},
    {"medicamento_id": 2, "farmacia_id": 2, "precio": 6.80},
    {"medicamento_id": 2, "farmacia_id": 3, "precio": 7.00},
    {"medicamento_id": 3, "farmacia_id": 1, "precio": 12.50},
    {"medicamento_id": 3, "farmacia_id": 2, "precio": 12.00},
    {"medicamento_id": 3, "farmacia_id": 3, "precio": 12.75},
]

@app.get("/precios")
def obtener_precios(medicamento_id: int, farmacia_id: int):
    for precio in precios:
        if precio["medicamento_id"] == medicamento_id and precio["farmacia_id"] == farmacia_id:
            return precio
    return {"mensaje": "Precio no encontrado."} 