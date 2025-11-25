# ingest_api/main.py
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List

# Importar nuestros módulos
from database import engine, get_db
from models import Telemetry, Alert
from schemas import TelemetryCreate, AlertResponse
from detector import detector

# Cargar variables de entorno
load_dotenv()

# Crear tablas en la base de datos si no existen
Telemetry.metadata.create_all(bind=engine)
Alert.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title="GreenDelivery - API de Ingesta",
    description="API para ingestar telemetría y detectar incidentes",
    version="2.0.0"
)


# ==============================================
# ENDPOINTS
# ==============================================

@app.get("/health")
def health_check():
    """
    Verificar que la API está funcionando
    """
    return {
        "status": "ok",
        "service": "GreenDelivery Ingest API",
        "version": "2.0.0"
    }


@app.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_data(data: TelemetryCreate, db: Session = Depends(get_db)):
    """
    Endpoint principal: recibe telemetría, detecta incidentes y guarda todo.
    
    Flujo:
    1. Validar datos (automático con Pydantic)
    2. Detectar si hay incidente
    3. Guardar telemetría en BD
    4. Si hay alerta, guardar alerta en BD
    """
    try:
        # ==========================================
        # PASO 1: Guardar telemetría
        # ==========================================
        db_telemetry = Telemetry(
            id_paquete=data.id_paquete,
            timestamp=data.timestamp,
            temperatura=data.temperatura,
            fuerza_g=data.fuerza_g,
            inclinacion=data.inclinacion,
            humedad=data.humedad,
            oxigeno=data.oxigeno,
            vapores=data.vapores,
            iluminacion=data.iluminacion,
            vibracion=data.vibracion
        )
        db.add(db_telemetry)
        db.commit()
        db.refresh(db_telemetry)
        
        # ==========================================
        # PASO 2: Detectar incidentes
        # ==========================================
        alerta_nueva, alerta_actualizada = detector.procesar_evento(data.dict())
        
        alerta_id = None
        alerta_actualizada_id = None
        
        # Si hay una NUEVA alerta
        if alerta_nueva:
            db_alert = Alert(
                id_paquete=alerta_nueva['id_paquete'],
                tipo_incidente=alerta_nueva['tipo_incidente'],
                timestamp_inicio=alerta_nueva['timestamp_inicio'],
                num_eventos=alerta_nueva['num_eventos'],
                valor_max=alerta_nueva['valor_max'],
                valor_promedio=alerta_nueva['valor_promedio'],
                detalles=alerta_nueva.get('detalles')
            )
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            alerta_id = db_alert.id
            
            # Guardar el ID de la alerta en el detector para poder actualizarla después
            detector.guardar_id_alerta(
                alerta_nueva['id_paquete'],
                alerta_nueva['tipo_incidente'],
                db_alert.id
            )
            
            print(f"🚨 Alerta guardada: ID={alerta_id}, tipo={alerta_nueva['tipo_incidente']}")
        
        # Si un incidente TERMINÓ (actualizar timestamp_fin)
        if alerta_actualizada and alerta_actualizada['alert_id']:
            alert_to_update = db.query(Alert).filter(
                Alert.id == alerta_actualizada['alert_id']
            ).first()
            
            if alert_to_update:
                alert_to_update.timestamp_fin = alerta_actualizada['timestamp_fin']
                alert_to_update.num_eventos = alerta_actualizada['num_eventos_final']
                alert_to_update.valor_max = alerta_actualizada['valor_max_final']
                alert_to_update.valor_promedio = alerta_actualizada['valor_promedio_final']
                db.commit()
                alerta_actualizada_id = alert_to_update.id
                
                print(f"✅ Alerta actualizada: ID={alerta_actualizada_id}, fin={alerta_actualizada['timestamp_fin']}")
        
        # ==========================================
        # PASO 3: Devolver respuesta
        # ==========================================
        response = {
            "status": "success",
            "telemetry_id": db_telemetry.id,
            "id_paquete": data.id_paquete
        }
        
        if alerta_id:
            response["alert_created"] = True
            response["alert_id"] = alerta_id
            response["alert_type"] = alerta_nueva['tipo_incidente']
        else:
            response["alert_created"] = False
        
        if alerta_actualizada_id:
            response["alert_updated"] = True
            response["alert_updated_id"] = alerta_actualizada_id
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al procesar datos: {str(e)}"
        )


@app.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Obtener todas las alertas registradas
    
    Parámetros:
    - skip: número de alertas a saltar (para paginación)
    - limit: número máximo de alertas a devolver
    """
    alerts = db.query(Alert)\
        .order_by(Alert.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return alerts


@app.get("/alerts/{id_paquete}")
def get_alerts_by_package(id_paquete: str, db: Session = Depends(get_db)):
    """
    Obtener todas las alertas de un paquete específico
    """
    alerts = db.query(Alert)\
        .filter(Alert.id_paquete == id_paquete)\
        .order_by(Alert.created_at.desc())\
        .all()
    
    if not alerts:
        return {
            "id_paquete": id_paquete,
            "total_alertas": 0,
            "alertas": []
        }
    
    return {
        "id_paquete": id_paquete,
        "total_alertas": len(alerts),
        "alertas": alerts
    }


@app.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """
    Obtener estadísticas generales del sistema
    """
    total_telemetry = db.query(Telemetry).count()
    total_alerts = db.query(Alert).count()
    
    # Contar alertas por tipo
    alerts_by_type = db.query(
        Alert.tipo_incidente,
        db.func.count(Alert.id)
    ).group_by(Alert.tipo_incidente).all()
    
    return {
        "total_eventos_telemetria": total_telemetry,
        "total_alertas": total_alerts,
        "alertas_por_tipo": {tipo: count for tipo, count in alerts_by_type},
        "estado_detector": {
            paquete_id: detector.obtener_estado(paquete_id)
            for paquete_id in detector.estados.keys()
        }
    }


@app.post("/detector/reset")
def reset_detector():
    """
    Reiniciar el detector (útil para testing)
    """
    detector.reiniciar()
    return {"status": "ok", "message": "Detector reiniciado"}


@app.get("/")
def root():
    """Página de inicio"""
    return {
        "message": "GreenDelivery Ingest API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "ingest": "POST /ingest",
            "alerts": "GET /alerts",
            "alerts_by_package": "GET /alerts/{id_paquete}",
            "stats": "GET /stats",
            "reset_detector": "POST /detector/reset"
        }
    }