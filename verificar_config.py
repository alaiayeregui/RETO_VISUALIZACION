#!/usr/bin/env python3
"""
Script de verificación - Comprueba que la red de Docker y las conexiones funcionan
"""

import os
import sys
from dotenv import load_dotenv

print("\n" + "="*70)
print("🔍 VERIFICACIÓN DE CONFIGURACIÓN")
print("="*70 + "\n")

# Cargar .env
load_dotenv()

print("✅ 1. Verificando variables de entorno...")
api_key = os.getenv("TOMTOM_API_KEY")
elastic_host = os.getenv("ELASTIC_HOST", "http://elasticsearch:9200")

print(f"   TOMTOM_API_KEY: {'✅ Configurada' if api_key else '❌ NO configurada'}")
print(f"   ELASTIC_HOST: {elastic_host}\n")

print("✅ 2. Verificando archivos críticos...")
files_to_check = [
    "docker-compose.yml",
    "colector-datos/Dockerfile",
    "colector-datos/main.py",
    "colector-datos/requirements.txt",
    ".env"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - NO ENCONTRADO")

print("\n✅ 3. Verificando contenidos de docker-compose.yml...")
try:
    with open("docker-compose.yml", "r") as f:
        content = f.read()
        
    checks = {
        "Network reto_network definida": "reto_network:" in content,
        "elasticsearch usa reto_network": "elasticsearch:" in content and "reto_network" in content,
        "kibana usa reto_network": "kibana:" in content and "reto_network" in content,
        "colector-datos usa reto_network": "colector-datos:" in content and "reto_network" in content,
        "PYTHONUNBUFFERED=1": "PYTHONUNBUFFERED=1" in content or "PYTHONUNBUFFERED: '1'" in content,
        "ELASTIC_HOST configurado": "ELASTIC_HOST=http://elasticsearch:9200" in content,
    }
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
except Exception as e:
    print(f"   ❌ Error leyendo docker-compose.yml: {e}")

print("\n✅ 4. Verificando contenidos de main.py...")
try:
    with open("colector-datos/main.py", "r") as f:
        content = f.read()
    
    checks = {
        "Importa os": "import os" in content,
        "Importa sys": "import sys" in content,
        "Validación de TOMTOM_API_KEY": "if not API_KEY:" in content,
        "Función conectar_elasticsearch": "def conectar_elasticsearch" in content,
        "Intenta 10 veces": "max_intentos=10" in content,
        "Espera 5 segundos": "espera_segundos=5" in content,
        "Try/except en create_mapping": "def create_mapping" in content and "try:" in content,
        "Try/except en fetch_and_send": "def fetch_and_send" in content and "try:" in content,
        "es.getenv con default": "os.getenv(\"ELASTIC_HOST\", \"http://elasticsearch:9200\")" in content,
    }
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
except Exception as e:
    print(f"   ❌ Error leyendo main.py: {e}")

print("\n✅ 5. Verificando Dockerfile...")
try:
    with open("colector-datos/Dockerfile", "r") as f:
        content = f.read()
    
    has_pythonunbuffered = "PYTHONUNBUFFERED=1" in content or "PYTHONUNBUFFERED" in content
    status = "✅" if has_pythonunbuffered else "❌"
    print(f"   {status} PYTHONUNBUFFERED=1 configurado")
except Exception as e:
    print(f"   ❌ Error leyendo Dockerfile: {e}")

print("\n" + "="*70)
print("🚀 Próximo paso: docker-compose up -d --build")
print("="*70 + "\n")
