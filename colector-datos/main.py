import requests
import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import time

load_dotenv()

# Configuración
API_KEY = os.getenv('TOMTOM_API_KEY')
ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'http://elasticsearch:9200')
# Para Flow usamos un punto central y un zoom (z10 es ciudad, z18 es calle)
LAT, LON = 40.4167, -3.7033 

es = Elasticsearch(ELASTIC_HOST)

# ... después de definir 'es' ...

# Borramos por si acaso para empezar de cero (opcional si ya hiciste el DELETE)
# es.indices.delete(index="traffic-flow", ignore=)

mapping = {
    "mappings": {
        "properties": {
            "location": { "type": "geo_point" },  # ESTO ES LO VITAL
            "@timestamp": { "type": "date" },
            "congestion_level": { "type": "float" }
        }
    }
}

if not es.indices.exists(index="traffic-flow"):
    es.indices.create(index="traffic-flow", body=mapping)
    print("✅ Índice creado con soporte para Mapas")
def get_traffic_flow():
    # Endpoint de Flow Segment Data
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={LAT},{LON}&key={API_KEY}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('flowSegmentData', {})
        
        # Calculamos la congestión (0 a 100)
        curr = data.get('currentSpeed', 0)
        free = data.get('freeFlowSpeed', 1)
        congestion = max(0, 100 - (curr / free * 100))
        
        # Estructura para Elasticsearch
        document = {
            "@timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "location": {"lat": LAT, "lon": LON},
            "current_speed": curr,
            "free_flow_speed": free,
            "congestion_level": round(congestion, 2),
            "travel_time_sec": data.get('currentTravelTime'),
            "road_type": data.get('frc')
        }
        return document
    return None

# Bucle principal simplificado
while True:
    flow_data = get_traffic_flow()
    if flow_data:
        res = es.index(index="traffic-flow", document=flow_data)
        print(f"✅ Datos de flujo indexados. Congestión actual: {flow_data['congestion_level']}%")
    time.sleep(60) # Consultar cada minuto