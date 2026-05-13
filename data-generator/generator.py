#!/usr/bin/env python3
"""
Generador de datos de tráfico aéreo para Elasticsearch.
Simula vuelos con posición, altitud, velocidad y estado de vuelo.
"""

import os
import time
import random
import logging
import math
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── Configuración desde variables de entorno ──────────────────────────────────
ELASTIC_HOST     = os.getenv("ELASTIC_HOST", "https://localhost:9200")
ELASTIC_USER     = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")
CA_CERT          = os.getenv("CA_CERT", "/certs/ca/ca.crt")
INTERVAL         = int(os.getenv("INTERVAL_SECONDS", "5"))
INDEX_NAME       = "air-traffic"

# ─── Aeropuertos simulados ────────────────────────────────────────────────────
AIRPORTS = [
    {"iata": "LEBL", "name": "Aeropuerto de Barcelona", "city": "Barcelona", "lat": 41.2974, "lon": 2.0833},
    {"iata": "LEMD", "name": "Aeropuerto de Madrid-Barajas", "city": "Madrid", "lat": 40.4774, "lon": -3.5626},
    {"iata": "LEMG", "name": "Aeropuerto de Málaga", "city": "Málaga", "lat": 36.6749, "lon": -4.4991},
    {"iata": "EGLL", "name": "Aeropuerto de Londres-Heathrow", "city": "Londres", "lat": 51.4700, "lon": -0.4543},
    {"iata": "LFPG", "name": "Aeropuerto de París-Charles de Gaulle", "city": "París", "lat": 49.0097, "lon": 2.5479},
    {"iata": "LEPA", "name": "Aeropuerto de Palma de Mallorca", "city": "Palma", "lat": 39.5517, "lon": 2.7386},
    {"iata": "LEBL", "name": "Aeropuerto de Barcelona-El Prat", "city": "Barcelona", "lat": 41.2974, "lon": 2.0833},
    {"iata": "LEVC", "name": "Aeropuerto de Valencia", "city": "Valencia", "lat": 39.4891, "lon": -0.4810},
]

AIRLINES = [
    {"code": "IB", "name": "Iberia"},
    {"code": "BA", "name": "British Airways"},
    {"code": "AF", "name": "Air France"},
    {"code": "VY", "name": "Vueling"},
    {"code": "KL", "name": "KLM"},
    {"code": "LH", "name": "Lufthansa"},
]

AIRCRAFT_TYPES = [
    "A320", "A321", "B737", "B787", "A330", "A350", "A220", "E190"
]

FLIGHT_STATUSES = ["enroute", "departing", "arriving", "landed", "delayed"]
SECTORS = ["Iberia", "Europa", "Atlántico", "Mediterráneo"]


def create_es_client() -> Elasticsearch:
    """Crea y devuelve un cliente Elasticsearch con TLS y autenticación."""
    for attempt in range(1, 11):
        try:
            es = Elasticsearch(
                ELASTIC_HOST,
                basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
                ca_certs=CA_CERT,
                verify_certs=True,
            )
            if es.ping():
                log.info("✅ Conectado a Elasticsearch en %s", ELASTIC_HOST)
                return es
        except Exception as exc:
            log.warning("Intento %d/10 fallido: %s. Reintentando en 10 s…", attempt, exc)
            time.sleep(10)
    raise RuntimeError("No se pudo conectar a Elasticsearch tras 10 intentos.")


def create_index(es: Elasticsearch) -> None:
    """Crea el índice con el mapping correcto si no existe."""
    if es.indices.exists(index=INDEX_NAME):
        log.info("Índice '%s' ya existe.", INDEX_NAME)
        return

    mapping = {
        "mappings": {
            "properties": {
                "@timestamp":          {"type": "date"},
                "flight_id":           {"type": "keyword"},
                "airline":             {"type": "keyword"},
                "callsign":            {"type": "keyword"},
                "aircraft_type":       {"type": "keyword"},
                "origin":              {"type": "keyword"},
                "destination":         {"type": "keyword"},
                "status":              {"type": "keyword"},
                "sector":              {"type": "keyword"},
                "position":            {"type": "geo_point"},
                "altitude_ft":         {"type": "float"},
                "speed_kt":            {"type": "float"},
                "heading":             {"type": "float"},
                "vertical_rate_fpm":   {"type": "float"},
                "alert":               {"type": "boolean"},
                "on_time":             {"type": "boolean"},
            }
        },
        "settings": {
            "number_of_shards":   1,
            "number_of_replicas": 0,
        },
    }

    es.indices.create(index=INDEX_NAME, body=mapping)
    log.info("✅ Índice '%s' creado con geo_point.", INDEX_NAME)


def haversine_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula el rumbo entre dos coordenadas en grados."""
    dy = math.radians(lat2 - lat1)
    dx = math.radians(lon2 - lon1)
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    y = math.sin(dx) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dx)
    heading = (math.degrees(math.atan2(y, x)) + 360) % 360
    return round(heading, 1)


def interpolate_position(origin: dict, destination: dict, progress: float) -> dict:
    """Interpolación simple entre origen y destino con ligera deriva."""
    lat = origin["lat"] + (destination["lat"] - origin["lat"]) * progress
    lon = origin["lon"] + (destination["lon"] - origin["lon"]) * progress
    return {
        "lat": lat + random.uniform(-0.05, 0.05),
        "lon": lon + random.uniform(-0.05, 0.05),
    }


def generate_flight_id() -> str:
    airline = random.choice(AIRLINES)
    number = random.randint(100, 9999)
    return f"{airline['code']}{number}", airline["name"]


def generate_flight() -> dict:
    origin, destination = random.sample(AIRPORTS, 2)
    flight_id, airline_name = generate_flight_id()
    aircraft = random.choice(AIRCRAFT_TYPES)
    progress = random.random()
    heading = haversine_heading(origin["lat"], origin["lon"], destination["lat"], destination["lon"])

    if progress < 0.1:
        status = "departing"
        altitude = random.uniform(500, 8000)
        speed = random.uniform(50, 180)
        vertical_rate = random.uniform(1000, 2500)
    elif progress > 0.9:
        status = "arriving"
        altitude = random.uniform(1200, 9000)
        speed = random.uniform(140, 220)
        vertical_rate = random.uniform(-2500, -500)
    else:
        status = random.choices(FLIGHT_STATUSES, weights=[5, 1, 1, 0.5, 0.5], k=1)[0]
        altitude = random.uniform(28000, 38000)
        speed = random.uniform(420, 520)
        vertical_rate = random.uniform(-500, 500)

    if status == "landed":
        altitude = random.uniform(0, 200)
        speed = random.uniform(0, 40)
        vertical_rate = random.uniform(-500, 500)

    position = interpolate_position(origin, destination, progress)
    on_time = random.random() > 0.1
    alert = (
        altitude < 1200 and status == "enroute"
        or speed > 620
        or (status == "arriving" and altitude > 10000)
    )

    return {
        "@timestamp":        datetime.now(timezone.utc).isoformat(),
        "flight_id":         flight_id,
        "airline":           airline_name,
        "callsign":          flight_id,
        "aircraft_type":     aircraft,
        "origin":            origin["iata"],
        "destination":       destination["iata"],
        "status":            status,
        "sector":            random.choice(SECTORS),
        "position":          position,
        "altitude_ft":       round(altitude, 1),
        "speed_kt":          round(speed, 1),
        "heading":           heading,
        "vertical_rate_fpm": round(vertical_rate, 1),
        "alert":             alert,
        "on_time":           on_time,
    }


def main() -> None:
    es = create_es_client()
    create_index(es)

    log.info("🚀 Iniciando generación de datos de tráfico aéreo cada %d segundos…", INTERVAL)
    log.info("   Aeropuertos: %d | Aerolíneas: %d", len(AIRPORTS), len(AIRLINES))

    while True:
        docs_sent = 0
        num_flights = random.randint(10, 18)
        for _ in range(num_flights):
            doc = generate_flight()
            try:
                es.index(index=INDEX_NAME, document=doc)
                docs_sent += 1
                if doc["alert"]:
                    log.warning(
                        "⚠️ ALERTA | %s %s → %s | %s | alt=%.0fft vel=%.0fkt",
                        doc["callsign"], doc["origin"], doc["destination"], doc["status"],
                        doc["altitude_ft"], doc["speed_kt"],
                    )
            except Exception as exc:
                log.error("Error al indexar documento: %s", exc)

        log.info("✅ %d documentos enviados a '%s'", docs_sent, INDEX_NAME)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
