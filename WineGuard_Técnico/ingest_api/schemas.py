# ingest_api/schemas.py
from pydantic import BaseModel, validator
from typing import Optional

class TelemetryCreate(BaseModel):
    """Esquema para recibir datos de telemetría"""
    id_paquete: str
    timestamp: str
    temperatura: float
    fuerza_g: float
    inclinacion: float
    humedad: float
    oxigeno: float
    vapores: float
    iluminacion: float
    vibracion: float

    @validator('temperatura')
    def temperatura_plausible(cls, v):
        if v < -20 or v > 50:
            raise ValueError('Temperatura fuera de rango plausible (-20 a 50°C)')
        return v

    @validator('fuerza_g')
    def fuerza_g_plausible(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Fuerza G fuera de rango físico (0 a 10G)')
        return v

    @validator('inclinacion')
    def inclinacion_plausible(cls, v):
        if v < -90 or v > 90:
            raise ValueError('Inclinación fuera de rango (-90 a 90°)')
        return v

    @validator('humedad')
    def humedad_plausible(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Humedad fuera de rango (0 a 100%)')
        return v


class AlertResponse(BaseModel):
    """Esquema para devolver alertas"""
    id: int
    id_paquete: str
    tipo_incidente: str
    timestamp_inicio: str
    timestamp_fin: Optional[str] = None
    num_eventos: int
    valor_max: float
    valor_promedio: Optional[float] = None
    created_at: str

    class Config:
        from_attributes = True  # Para SQLAlchemy 2.0+