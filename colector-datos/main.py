import os
import time
import requests
from elasticsearch import Elasticsearch
from datetime import datetime
from dotenv import load_dotenv

# 1. Carga de variables de entorno
load_dotenv() 

# Usamos nombres consistentes
API_KEY = os.getenv("TOMTOM_API_KEY")
ELASTIC_URL = os.getenv("ELASTIC_HOST", "http://localhost:9200")
INDEX_NAME = "traffic-history"

# Coordenadas de ejemplo (Madrid)
BBOX = "-3.81,40.35,-3.58,40.52" 

# 2. Inicialización del cliente de Elastic
# Usamos la variable ELASTIC_URL que definimos arriba
es = Elasticsearch(ELASTIC_URL)

def create_mapping():
    """Define el tipo geo_point para poder usar mapas en Kibana"""
    try:
        if not es.indices.exists(index=INDEX_NAME):
            mapping = {
                "mappings": {
                    "properties": {
                        "location": {"type": "geo_point"},
                        "timestamp": {"type": "date"},
                        "severity": {"type": "integer"},
                        "delay": {"type": "integer"},
                        "description": {"type": "text"},
                        "type": {"type": "integer"}
                    }
                }
            }
            # En la v8 de la librería, se recomienda usar 'body' o argumentos directos
            es.indices.create(index=INDEX_NAME, body=mapping)
            print(f"✅ Índice '{INDEX_NAME}' creado con mapping de geolocalización.")
        else:
            print(f"ℹ️ El índice '{INDEX_NAME}' ya existe. Saltando creación.")
    except Exception as e:
        print(f"❌ Error al crear el mapping: {e}")

def fetch_and_send():
    # Usamos la variable API_KEY corregida
    url = f"https://api.tomtom.com/traffic/services/4/incidentDetails/s3/{BBOX}/10/-1/json?key={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Lanza error si la API falla (ej. 403 Forbidden)
        data = response.json()
        
        if "tm" in data and "poi" in data["tm"]:
            for incident in data["tm"]["poi"]:
                doc = {
                    "timestamp": datetime.utcnow(),
                    "description": incident.get("d", "Sin descripción"),
                    "severity": incident.get("ic", 0), 
                    "delay": incident.get("dl", 0), 
                    "location": {
                        "lat": incident["p"]["y"],
                        "lon": incident["p"]["x"]
                    },
                    "type": incident.get("ty", 0)
                }
                
                es.index(index=INDEX_NAME, document=doc)
            
            print(f"🚀 {datetime.now().strftime('%H:%M:%S')} - Procesadas {len(data['tm']['poi'])} incidencias.")
        else:
            print("⚠️ No hay incidencias activas en este momento.")
            
    except Exception as e:
        print(f"❌ Error en la descarga/envío: {e}")

if __name__ == "__main__":
    # Espera un poco a que Elastic esté listo (útil cuando arrancas con docker-compose)
    print("Esperando a que Elasticsearch arranque...")
    time.sleep(10) 
    
    create_mapping()
    
    print("Iniciando bucle de captura...")
    while True:
        fetch_and_send()
        # Tiempo de espera (300 seg = 5 min)
        time.sleep(300)