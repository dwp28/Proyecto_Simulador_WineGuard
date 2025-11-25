# ingest_api/detector.py
"""
Detector de incidentes con memoria MEJORADO.
- Rastrea el inicio Y fin de incidentes
- Calcula promedios durante el incidente
- Cuenta TODOS los eventos del incidente
"""
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json


# ==============================================
# CONFIGURACIÓN DE UMBRALES
# ==============================================
UMBRAL_TEMPERATURA = 8.0        # °C - Por encima de esto es problema
UMBRAL_FUERZA_G = 2.5           # G - Por encima de esto es impacto fuerte
UMBRAL_INCLINACION = 30.0       # grados - Por encima de esto está volcado
N_EVENTOS_CONSECUTIVOS = 3      # Cuántos eventos seguidos para confirmar


@dataclass
class EstadoPaquete:
    """Estado actual de un paquete (memoria mejorada)"""
    # Temperatura
    eventos_temp_alta: int = 0
    alerta_temp_id: Optional[int] = None  # ID de la alerta activa
    timestamp_inicio_temp: Optional[str] = None
    valores_temp: List[float] = field(default_factory=list)  # Historial de valores
    
    # Choque
    eventos_choque: int = 0
    alerta_choque_id: Optional[int] = None  # ID de la alerta activa
    timestamp_inicio_choque: Optional[str] = None
    valores_fuerza_g: List[float] = field(default_factory=list)  # Historial


class DetectorIncidentes:
    """
    Clase que mantiene el estado de todos los paquetes
    y detecta incidentes sostenidos con métricas mejoradas.
    """
    
    def __init__(self):
        # Diccionario para guardar el estado de cada paquete
        self.estados: Dict[str, EstadoPaquete] = {}
    
    def procesar_evento(self, data: dict) -> tuple[Optional[dict], Optional[dict]]:
        """
        Procesa un evento de telemetría.
        
        Returns:
            (alerta_nueva, alerta_actualizada)
            - alerta_nueva: dict si se detecta un NUEVO incidente
            - alerta_actualizada: dict si un incidente TERMINA (para actualizar timestamp_fin)
        """
        id_paquete = data['id_paquete']
        
        # Crear estado si es la primera vez que vemos este paquete
        if id_paquete not in self.estados:
            self.estados[id_paquete] = EstadoPaquete()
        
        estado = self.estados[id_paquete]
        alerta_nueva = None
        alerta_actualizada = None
        
        # ==========================================
        # DETECCIÓN DE TEMPERATURA ALTA
        # ==========================================
        if data['temperatura'] > UMBRAL_TEMPERATURA:
            # Evento anómalo
            estado.eventos_temp_alta += 1
            estado.valores_temp.append(data['temperatura'])
            
            # Guardar timestamp del primer evento
            if estado.eventos_temp_alta == 1:
                estado.timestamp_inicio_temp = data['timestamp']
            
            # ¿Alcanzamos el umbral para crear alerta?
            if estado.eventos_temp_alta == N_EVENTOS_CONSECUTIVOS:
                valor_max = max(estado.valores_temp)
                valor_promedio = sum(estado.valores_temp) / len(estado.valores_temp)
                
                print(f"🔥 ALERTA NUEVA: {id_paquete} - Temperatura alta sostenida")
                print(f"   └─ Eventos: {estado.eventos_temp_alta}")
                print(f"   └─ Max: {valor_max:.2f}°C | Promedio: {valor_promedio:.2f}°C")
                
                alerta_nueva = {
                    'id_paquete': id_paquete,
                    'tipo_incidente': 'temperatura_alta',
                    'timestamp_inicio': estado.timestamp_inicio_temp,
                    'num_eventos': estado.eventos_temp_alta,
                    'valor_max': valor_max,
                    'valor_promedio': valor_promedio,
                    'detalles': json.dumps({
                        'umbral': UMBRAL_TEMPERATURA,
                        'valores': estado.valores_temp
                    })
                }
        
        else:
            # Temperatura normalizada
            if estado.eventos_temp_alta >= N_EVENTOS_CONSECUTIVOS:
                # El incidente TERMINÓ - actualizar timestamp_fin
                valor_max = max(estado.valores_temp)
                valor_promedio = sum(estado.valores_temp) / len(estado.valores_temp)
                
                print(f"💚 INCIDENTE TEMPERATURA FINALIZADO: {id_paquete}")
                print(f"   └─ Duración: {estado.eventos_temp_alta} eventos")
                print(f"   └─ Max: {valor_max:.2f}°C | Promedio: {valor_promedio:.2f}°C")
                
                alerta_actualizada = {
                    'alert_id': estado.alerta_temp_id,
                    'timestamp_fin': data['timestamp'],
                    'num_eventos_final': estado.eventos_temp_alta,
                    'valor_max_final': valor_max,
                    'valor_promedio_final': valor_promedio
                }
            
            # Resetear estado
            estado.eventos_temp_alta = 0
            estado.valores_temp = []
            estado.timestamp_inicio_temp = None
            estado.alerta_temp_id = None
        
        # ==========================================
        # DETECCIÓN DE CHOQUE (fuerza_g + inclinación)
        # ==========================================
        if (data['fuerza_g'] > UMBRAL_FUERZA_G 
            and data['inclinacion'] > UMBRAL_INCLINACION):
            
            # Evento anómalo
            estado.eventos_choque += 1
            estado.valores_fuerza_g.append(data['fuerza_g'])
            
            # Guardar timestamp del primer evento
            if estado.eventos_choque == 1:
                estado.timestamp_inicio_choque = data['timestamp']
            
            # ¿Alcanzamos el umbral para crear alerta?
            if estado.eventos_choque == N_EVENTOS_CONSECUTIVOS and alerta_nueva is None:
                valor_max = max(estado.valores_fuerza_g)
                valor_promedio = sum(estado.valores_fuerza_g) / len(estado.valores_fuerza_g)
                
                print(f"💥 ALERTA NUEVA: {id_paquete} - Choque detectado")
                print(f"   └─ Eventos: {estado.eventos_choque}")
                print(f"   └─ Max: {valor_max:.2f}G | Promedio: {valor_promedio:.2f}G")
                
                alerta_nueva = {
                    'id_paquete': id_paquete,
                    'tipo_incidente': 'choque',
                    'timestamp_inicio': estado.timestamp_inicio_choque,
                    'num_eventos': estado.eventos_choque,
                    'valor_max': valor_max,
                    'valor_promedio': valor_promedio,
                    'detalles': json.dumps({
                        'umbral_fuerza_g': UMBRAL_FUERZA_G,
                        'umbral_inclinacion': UMBRAL_INCLINACION,
                        'fuerza_g_actual': data['fuerza_g'],
                        'inclinacion_actual': data['inclinacion'],
                        'valores_fuerza_g': estado.valores_fuerza_g
                    })
                }
        
        else:
            # Condiciones normalizadas
            if estado.eventos_choque >= N_EVENTOS_CONSECUTIVOS and alerta_actualizada is None:
                # El incidente TERMINÓ
                valor_max = max(estado.valores_fuerza_g)
                valor_promedio = sum(estado.valores_fuerza_g) / len(estado.valores_fuerza_g)
                
                print(f"💚 INCIDENTE CHOQUE FINALIZADO: {id_paquete}")
                print(f"   └─ Duración: {estado.eventos_choque} eventos")
                print(f"   └─ Max: {valor_max:.2f}G | Promedio: {valor_promedio:.2f}G")
                
                alerta_actualizada = {
                    'alert_id': estado.alerta_choque_id,
                    'timestamp_fin': data['timestamp'],
                    'num_eventos_final': estado.eventos_choque,
                    'valor_max_final': valor_max,
                    'valor_promedio_final': valor_promedio
                }
            
            # Resetear estado
            estado.eventos_choque = 0
            estado.valores_fuerza_g = []
            estado.timestamp_inicio_choque = None
            estado.alerta_choque_id = None
        
        return alerta_nueva, alerta_actualizada
    
    def guardar_id_alerta(self, id_paquete: str, tipo_incidente: str, alert_id: int):
        """Guardar el ID de una alerta para poder actualizarla después"""
        if id_paquete in self.estados:
            estado = self.estados[id_paquete]
            if tipo_incidente == 'temperatura_alta':
                estado.alerta_temp_id = alert_id
            elif tipo_incidente == 'choque':
                estado.alerta_choque_id = alert_id
    
    def obtener_estado(self, id_paquete: str) -> Optional[dict]:
        """Devuelve el estado actual de un paquete (para debugging)"""
        if id_paquete not in self.estados:
            return None
        
        estado = self.estados[id_paquete]
        return {
            'eventos_temp_alta': estado.eventos_temp_alta,
            'eventos_choque': estado.eventos_choque,
            'alerta_temp_activa': estado.alerta_temp_id is not None,
            'alerta_choque_activa': estado.alerta_choque_id is not None
        }
    
    def reiniciar(self):
        """Reinicia todos los estados (útil para testing)"""
        self.estados = {}
        print("🔄 Detector reiniciado")


# Instancia global (Singleton)
detector = DetectorIncidentes()