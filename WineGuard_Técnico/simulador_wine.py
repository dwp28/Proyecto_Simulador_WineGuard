import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# ============================================
# CONFIGURACIÓN MQTT
# ============================================
BROKER = "test.mosquitto.org"  
PORT = 1883
TOPIC = "greendelivery/trackers/telemetry"

# ============================================
# PARÁMETROS DE LOS INCIDENTES
# ============================================
# Cuántos eventos normales antes del primer incidente
EVENTOS_ANTES_INCIDENTE_1 = 15  

# Cuántos eventos anómalos para el incidente de temperatura
EVENTOS_INCIDENTE_TEMPERATURA = 6  

# Cuántos eventos normales entre incidentes
EVENTOS_ENTRE_INCIDENTES = 20  

# Cuántos eventos anómalos para el incidente de choque
EVENTOS_INCIDENTE_CHOQUE = 4  

# Cuántos eventos normales después
EVENTOS_FINALES = 30

# Eventos especiales (falsos positivos y vibraciones)
EVENTO_PICO_EXTREMO_TEMP = 8      # En qué evento ocurre el pico de 28°C
EVENTOS_VIBRACION_ALTA = [12, 25]  # En qué eventos hay vibración alta

# ============================================
# ESTADO DEL SIMULADOR
# ============================================
evento_actual = 0

# Conectar al broker
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
print(f"✅ Conectado al broker MQTT: {BROKER}")
print(f"📡 Publicando en: {TOPIC}")
print("=" * 60)

def generar_datos_normales(id_paquete):
    """Genera datos normales para un paquete"""
    return {
        "id_paquete": id_paquete,
        "temperatura": round(random.uniform(4.0, 7.5), 2),      # Rango normal: 4-7.5°C
        "fuerza_g": round(random.uniform(0.1, 1.8), 2),         # Rango normal: 0.1-1.8G
        "inclinacion": round(random.uniform(0.0, 15.0), 2),     # Rango normal: 0-15°
        "humedad": round(random.uniform(50.0, 70.0), 2),        # Rango normal
        "oxigeno": round(random.uniform(19.0, 21.0), 2),        # Rango normal
        "vapores": round(random.uniform(0.0, 5.0), 2),          # Rango normal
        "iluminacion": round(random.uniform(0.0, 50.0), 2),     # Rango normal
        "vibracion": round(random.uniform(0.0, 2.0), 2),        # Rango normal
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def generar_incidente_temperatura(id_paquete):
    """Genera datos con temperatura ALTA (incidente)"""
    data = generar_datos_normales(id_paquete)
    data["temperatura"] = round(random.uniform(9.0, 12.0), 2)  # ¡MUY ALTA!
    return data

def generar_incidente_choque(id_paquete):
    """Genera datos de un CHOQUE (fuerza_g e inclinación altas)"""
    data = generar_datos_normales(id_paquete)
    data["fuerza_g"] = round(random.uniform(3.5, 5.0), 2)      # ¡IMPACTO FUERTE!
    data["inclinacion"] = round(random.uniform(45.0, 90.0), 2) # ¡VOLCADO!
    return data

def generar_paquete_caido(id_paquete):
    """Genera datos de un paquete caído (sin movimiento)"""
    data = generar_datos_normales(id_paquete)
    data["fuerza_g"] = 0.0          # Sin movimiento
    data["inclinacion"] = 0.0        # Plano
    data["vibracion"] = 0.0          # Sin vibración
    return data

# ============================================
# SIMULACIÓN PRINCIPAL
# ============================================
try:
    while True:
        evento_actual += 1
        
        # ========================================
        # FASE 1: Datos normales (todos los paquetes)
        # ========================================
        if evento_actual <= EVENTOS_ANTES_INCIDENTE_1:
            print(f"\n📦 Evento {evento_actual} - FASE NORMAL")
            paquetes = [
                generar_datos_normales("vino_tinto_001"),
                generar_datos_normales("vino_tinto_002"),
                generar_datos_normales("vino_tinto_003")
            ]
        
        # ========================================
        # FASE 2: INCIDENTE DE TEMPERATURA (paquete 001)
        # ========================================
        elif evento_actual <= EVENTOS_ANTES_INCIDENTE_1 + EVENTOS_INCIDENTE_TEMPERATURA:
            print(f"\n🔥 Evento {evento_actual} - ¡INCIDENTE TEMPERATURA! (paquete 001)")
            paquetes = [
                generar_incidente_temperatura("vino_tinto_001"),  # ¡PROBLEMA!
                generar_datos_normales("vino_tinto_002"),         # Normal
                generar_datos_normales("vino_tinto_003")          # Normal
            ]
        
        # ========================================
        # FASE 3: Recuperación (todos normales otra vez)
        # ========================================
        elif evento_actual <= EVENTOS_ANTES_INCIDENTE_1 + EVENTOS_INCIDENTE_TEMPERATURA + EVENTOS_ENTRE_INCIDENTES:
            print(f"\n💚 Evento {evento_actual} - Recuperación post-temperatura")
            paquetes = [
                generar_datos_normales("vino_tinto_001"),
                generar_datos_normales("vino_tinto_002"),
                generar_datos_normales("vino_tinto_003")
            ]
        
        # ========================================
        # FASE 4: INCIDENTE DE CHOQUE (paquete 002)
        # ========================================
        elif evento_actual <= EVENTOS_ANTES_INCIDENTE_1 + EVENTOS_INCIDENTE_TEMPERATURA + EVENTOS_ENTRE_INCIDENTES + EVENTOS_INCIDENTE_CHOQUE:
            print(f"\n💥 Evento {evento_actual} - ¡INCIDENTE CHOQUE! (paquete 002)")
            paquetes = [
                generar_datos_normales("vino_tinto_001"),         # Normal
                generar_incidente_choque("vino_tinto_002"),       # ¡PROBLEMA!
                generar_datos_normales("vino_tinto_003")          # Normal
            ]
        
        # ========================================
        # FASE 5: Paquete 002 caído (fuerza_g = 0, inclinación = 0)
        # ========================================
        elif evento_actual <= EVENTOS_ANTES_INCIDENTE_1 + EVENTOS_INCIDENTE_TEMPERATURA + EVENTOS_ENTRE_INCIDENTES + EVENTOS_INCIDENTE_CHOQUE + EVENTOS_FINALES:
            print(f"\n📍 Evento {evento_actual} - Paquete 002 CAÍDO (sin movimiento)")
            paquetes = [
                generar_datos_normales("vino_tinto_001"),         # Normal
                generar_paquete_caido("vino_tinto_002"),          # ¡CAÍDO!
                generar_datos_normales("vino_tinto_003")          # Normal
            ]
        
        # ========================================
        # FASE 6: Fin de la simulación
        # ========================================
        else:
            print("\n🏁 Simulación completa. Reiniciando...")
            evento_actual = 0
            time.sleep(5)
            continue
        
        # Publicar los 3 paquetes
        for data in paquetes:
            payload = json.dumps(data)
            client.publish(TOPIC, payload)
            print(f"   → {data['id_paquete']}: temp={data['temperatura']}°C, g={data['fuerza_g']}G, incl={data['inclinacion']}°")
        
        time.sleep(2)  # Esperar 2 segundos entre eventos

except KeyboardInterrupt:
    print("\n🛑 Simulador detenido.")
    client.disconnect()