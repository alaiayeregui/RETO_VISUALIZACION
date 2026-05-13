#!/usr/bin/env python3
"""
Script de diagnóstico para RETO_VISUALIZACION
Verifica que todas las conexiones funcionen correctamente
"""

import os
import sys
import requests
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

print("\n" + "="*70)
print("🔧 DIAGNÓSTICO - RETO_VISUALIZACION")
print("="*70 + "\n")

# Cargar variables
load_dotenv()

# 1. Verificar variables de entorno
print("[1/4] Verificando variables de entorno...")
api_key = os.getenv("TOMTOM_API_KEY")
elastic_host = os.getenv("ELASTIC_HOST", "http://localhost:9200")

if not api_key:
    print("❌ TOMTOM_API_KEY no configurada en .env")
    sys.exit(1)
else:
    print(f"✅ TOMTOM_API_KEY: {api_key[:5]}...{api_key[-5:]}")

print(f"✅ ELASTIC_HOST: {elastic_host}")

# 2. Probar conexión a Elasticsearch
print("\n[2/4] Probando conexión a Elasticsearch...")
try:
    es = Elasticsearch([elastic_host])
    info = es.info()
    print(f"✅ Conectado a Elasticsearch {info['version']['number']}")
    health = es.cluster.health()
    print(f"   📊 Salud del cluster: {health['status']}")
except Exception as e:
    print(f"❌ Error conectando a Elasticsearch: {e}")
    print(f"   ¿Está corriendo en {elastic_host}?")
    sys.exit(1)

# 3. Probar API de TomTom
print("\n[3/4] Probando API de TomTom...")
bbox = "-15.0,35.0,35.0,70.0"
url = f"https://api.tomtom.com/traffic/services/4/incidentDetails/s3/{bbox}/10/-1/json?key={api_key}"
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if "tm" in data and "poi" in data["tm"]:
        count = len(data["tm"]["poi"])
        print(f"✅ API respondió - {count} incidentes encontrados")
    else:
        print(f"⚠️ API respondió pero sin incidentes (puede ser normal)")
        
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print(f"❌ Error 401: TOMTOM_API_KEY inválida")
    else:
        print(f"❌ Error HTTP {e.response.status_code}: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error en TomTom API: {e}")
    sys.exit(1)

# 4. Verificar índice en Elasticsearch
print("\n[4/4] Verificando índice en Elasticsearch...")
index_name = "traffic-history"
try:
    exists = es.indices.exists(index=index_name)
    if exists:
        stats = es.indices.stats(index=index_name)
        doc_count = stats['indices'][index_name]['primaries']['docs']['count']
        print(f"✅ Índice '{index_name}' existe")
        print(f"   📊 Documentos: {doc_count}")
    else:
        print(f"⚠️ Índice '{index_name}' no existe (se creará al iniciar colector-datos)")
except Exception as e:
    print(f"❌ Error verificando índice: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ TODAS LAS PRUEBAS PASARON - Sistema listo para funcionar")
print("="*70 + "\n")
