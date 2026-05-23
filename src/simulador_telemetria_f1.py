import os
import math
import json
import time
import random
import pandas as pd
from datetime import datetime
from google.cloud import pubsub_v1
import fastf1

# 🎛️ CONFIGURACIÓN DEL PROYECTO
PROJECT_ID = "MI_ID_PROYECTO"  # ⚠️ Reemplaza con tu ID de GCP
TOPIC_ID = "telemetria-f1"

TEMPORADA = 2023
EVENTO = "Monza"
SESION_TIPO = "R"  # 'R' para Carrera (Race)

# 📁 PASO 1: Validación autónoma del directorio de caché
dir_cache = 'cache_fastf1'
if not os.path.exists(dir_cache):
    os.mkdir(dir_cache)
    print(f"📁 Carpeta '{dir_cache}' creada de forma autónoma.")

# 🛰️ PASO 2: Inicialización del cliente de Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

print("🔄 Cargando datos desde la API de FastF1...")

try:
    # 🏎️ Intento de carga de datos reales
    fastf1.Cache.enable_cache(dir_cache)
    session = fastf1.get_session(TEMPORADA, EVENTO, SESION_TIPO)
    session.load()
    laps = session.laps.pick_quicklaps()
    
    print("✅ Datos reales cargados. Iniciando streaming en vivo...")
    
except Exception as e:
# 🌍 PASO 3: Plan de contingencia por bloqueo de red en Cloud Shell
    print(f"⚠️ No se pudo conectar a la API externa (Error: {e}).")
    print("🚀 Activando generación masiva: 20 pilotos en pista...")
    
    import random # Necesario para generar variaciones entre pilotos

    # 👥 Catálogo de 20 pilotos (Nombre y Número)
    lista_pilotos = [
        ("VER", "1"), ("SAR", "2"), ("RIC", "3"), ("NOR", "4"), ("GAS", "10"),
        ("PER", "11"), ("ALO", "14"), ("LEC", "16"), ("STR", "18"), ("MAG", "20"),
        ("TSU", "22"), ("ALB", "23"), ("ZHO", "24"), ("HUL", "27"), ("OCO", "31"),
        ("HAM", "44"), ("SAI", "55"), ("RUS", "63"), ("BOT", "77"), ("PIA", "81")
    ]

    # 🧠 Diccionario para guardar el "estado" independiente de cada auto
    estado_pilotos = {}
    for nombre, numero in lista_pilotos:
        estado_pilotos[nombre] = {
            "numero": numero,
            "velocidad_anterior": 200.0,
            "fase_pista": random.uniform(0, 2 * math.pi), # Desfase para que no vayan pegados
            "rendimiento": random.uniform(0.95, 1.05)    # Pequeña variación de velocidad
        }

    total_vueltas = 3
    puntos_por_vuelta = 50
    
    for vuelta in range(1, total_vueltas + 1):
        print(f"\n🏁 Simulado: Iniciando Vuelta {vuelta} para la parrilla completa...")
        
        for i in range(puntos_por_vuelta):
            # 🕒 Calcula el timestamp UNA sola vez por ciclo para sincronizar a los 20
            timestamp_actual = str(pd.Timestamp.now())
            
            # 🏎️ Bucle interno: Procesa a cada piloto en el mismo "segundo"
            for nombre, estado in estado_pilotos.items():
                
                # 🔄 Progreso de la vuelta + el desfase individual del piloto
                progreso_base = (i / puntos_por_vuelta) * 2 * math.pi
                progreso_individual = progreso_base + estado["fase_pista"]
                
                # 📈 Cálculo ondulatorio de velocidad afectado por su rendimiento único
                velocidad = 200.0 + (110.0 * math.sin(progreso_individual * 3) * estado["rendimiento"])
                velocidad = max(80.0, min(velocidad, 360.0)) # Límites lógicos de F1
                
                rpm = 9000 + 3500 * math.sin(progreso_individual * 11)
                
                # 🔲 Lógica de pedales basada en la memoria individual del piloto
                if velocidad > estado["velocidad_anterior"]:
                    brake_application = False
                    throttle_application = min((velocidad - estado["velocidad_anterior"]) / 8, 1.0)
                else:
                    brake_application = True
                    throttle_application = 0.0
                    
                # Actualizar la memoria para el siguiente ciclo
                estado["velocidad_anterior"] = velocidad
                
                # 📦 Construcción del JSON individual
                mensaje = {
                    "race_id": f"{TEMPORADA}_{EVENTO.upper()}_SIM",
                    "driver": nombre,
                    "event_name": str(EVENTO),
                    "lap_number": int(vuelta),
                    "lap_time": "0 days 00:01:21.345000",
                    "position": 1, # Opcional: Calcular posiciones reales luego
                    "session_type": str(SESION_TIPO),
                    "driver_number": estado["numero"],
                    "lap_duration_ms": 81345,
                    "compound": "SOFT",
                    "season": int(TEMPORADA),
                    "speed_kmh": round(float(velocidad), 2),
                    "rpm": int(rpm),
                    "gear_selection": int(5 + math.sin(progreso_individual * 5) * 3),
                    "throttle_application": round(float(throttle_application), 2),
                    "brake_application": bool(brake_application),
                    "timestamp": timestamp_actual
                }
                
                # 📨 Enviar evento a Pub/Sub
                data_string = json.dumps(mensaje)
                publisher.publish(topic_path, data_string.encode("utf-8"))
            
            # Notificamos que el bloque de 20 mensajes salió exitosamente
            print(f"📡 Tick enviado -> 20 telemetrías publicadas al mismo tiempo.")
            
            # ⏱️ Pausa de 1 segundo aplicable a TODA LA PARRILLA antes del siguiente punto
            time.sleep(1)
