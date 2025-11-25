# ingest_api/models.py
from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from database import Base

class Telemetry(Base):
    """Tabla de telemetría - guarda todos los eventos de los sensores"""
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    id_paquete = Column(String, index=True)
    timestamp = Column(String)  # ISO 8601
    temperatura = Column(Float)
    fuerza_g = Column(Float)
    inclinacion = Column(Float)
    humedad = Column(Float)
    oxigeno = Column(Float)
    vapores = Column(Float)
    iluminacion = Column(Float)
    vibracion = Column(Float)


class Alert(Base):
    """Tabla de alertas - guarda solo los incidentes detectados"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    id_paquete = Column(String, index=True)
    tipo_incidente = Column(String)  # 'temperatura_alta', 'choque', etc.
    timestamp_inicio = Column(String)  # Cuándo empezó el problema
    timestamp_fin = Column(String, nullable=True)  # Cuándo terminó
    num_eventos = Column(Integer)  # TOTAL de eventos del incidente
    valor_max = Column(Float)  # Valor máximo registrado
    valor_promedio = Column(Float, nullable=True)  # Valor promedio del incidente
    detalles = Column(String, nullable=True)  # Info adicional (JSON string)
    created_at = Column(DateTime, default=datetime.utcnow)