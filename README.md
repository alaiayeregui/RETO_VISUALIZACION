# ✈️ Simulación de Tráfico Aéreo — Visualización con Elastic Stack

> **Reto: Visualización de Datos** · Desarrollo de aplicaciones para IoT · Universidad de Deusto  
> Elastic Stack 8.13 · Elasticsearch · Kibana · Docker Compose · Python

---

## 👥 Miembros del equipo

| Nombre |
|--------|
| *Alaia Yeregui* |
| *Asier Sánchez* |

---

## 📋 Descripción del proyecto

Plataforma de monitorización de **tráfico aéreo en tiempo real** que simula vuelos entre aeropuertos españoles y europeos. Cada 5 segundos se generan entre 10 y 18 vuelos con posición GPS, altitud, velocidad, aerolínea y estado, que se indexan en Elasticsearch y se visualizan en Kibana con un **mapa geográfico interactivo**.

### Arquitectura

```
┌─────────────────┐     HTTPS/TLS      ┌──────────────────────┐
│  Data Generator │ ─────────────────▶ │   Elasticsearch 8.13 │
│  (Python)       │                    │   + TLS + Auth        │
└─────────────────┘                    └──────────┬───────────┘
                                                   │
                                       ┌──────────▼───────────┐
                                       │       Kibana          │
                                       │  Dashboard + Mapas    │
                                       └──────────────────────┘
```

### Aeropuertos simulados

| IATA | Aeropuerto | Ciudad |
|------|-----------|--------|
| LEBL | Barcelona-El Prat | Barcelona |
| LEMD | Madrid-Barajas | Madrid |
| LEMG | Málaga | Málaga |
| LEPA | Palma de Mallorca | Palma |
| LEVC | Valencia | Valencia |
| EGLL | Londres-Heathrow | Londres |
| LFPG | París-Charles de Gaulle | París |

### Aerolíneas simuladas

Iberia (IB), British Airways (BA), Air France (AF), Vueling (VY), KLM (KL), Lufthansa (LH)

### Datos generados por vuelo

| Campo | Descripción |
|-------|-------------|
| `@timestamp` | Marca temporal UTC |
| `flight_id` / `callsign` | Identificador único del vuelo (ej: IB1234) |
| `airline` / `aircraft_type` | Aerolínea y tipo de avión (A320, B737…) |
| `origin` / `destination` | Código IATA de aeropuerto origen y destino |
| `position` | Coordenadas GPS interpoladas (`geo_point`) |
| `altitude_ft` | Altitud en pies |
| `speed_kt` | Velocidad en nudos |
| `heading` | Rumbo en grados |
| `vertical_rate_fpm` | Tasa de ascenso/descenso en pies por minuto |
| `status` | `enroute`, `departing`, `arriving`, `landed`, `delayed` |
| `alert` | `true` si hay condición anómala (baja altitud, exceso de velocidad…) |
| `on_time` | `true` si el vuelo va puntual |

---

## 🚀 Instrucciones de uso

### Prerrequisitos

- Docker Engine ≥ 24
- Docker Compose v2
- 4 GB de RAM disponible
- Puertos `9200` y `5601` libres

### 1 — Clonar y configurar

```bash
git clone <url-del-repo>
cd elastic-iot

# (Opcional) Editar contraseñas en .env antes de arrancar
nano .env
```

### 2 — Arrancar el stack completo

```bash
docker compose up -d
```

El arranque sigue este orden automáticamente:
1. `setup` — genera certificados TLS autofirmados con CA propia
2. `elasticsearch` — nodo único con seguridad y TLS activados
3. `kibana` — interfaz web
4. `data-generator` — empieza a enviar vuelos cada 5 segundos

### 3 — Configurar contraseña de kibana_system (primera vez)

```bash
bash setup/setup-passwords.sh
```

### 4 — Acceder a Kibana

```
http://localhost:5601
Usuario:     elastic
Contraseña:  ElasticIoT2024!   (o la que hayas configurado en .env)
```

### 5 — Crear el Data View en Kibana

1. Menú → **Management** → **Data Views**
2. Crear data view con patrón `air-traffic*`
3. Campo de tiempo: `@timestamp`

### 6 — Crear el Dashboard con Mapa

#### Mapa geográfico de vuelos
1. **Maps** → Create map
2. Add layer → **Documents** → selecciona `air-traffic*`
3. Geospatial field: `position`
4. Tooltip fields: `flight_id`, `airline`, `altitude_ft`, `status`, `alert`
5. Style: colorear por `alert` (rojo = alerta, verde = normal)

#### Gráficos adicionales recomendados
- **Line chart** de `altitude_ft` agrupado por `status`
- **Bar chart** de alertas agrupadas por `airline`
- **Donut** de distribución por `status`
- **Data table** de vuelos con `alert: true`
- **Metric** con contador total de alertas activas

### 7 — Verificar Elasticsearch directamente

```bash
# Ver el estado del cluster
curl -k -u elastic:ElasticIoT2024! https://localhost:9200

# Ver los últimos 5 vuelos
curl -k -u elastic:ElasticIoT2024! \
  "https://localhost:9200/air-traffic/_search?size=5&sort=@timestamp:desc&pretty"

# Contar vuelos con alerta activa
curl -k -u elastic:ElasticIoT2024! \
  "https://localhost:9200/air-traffic/_count?q=alert:true&pretty"
```

### 8 — Detener el stack

```bash
docker compose down       # mantiene los datos
docker compose down -v    # elimina también los volúmenes (reset completo)
```

---

## 🔒 Seguridad implementada

| Característica | Detalle |
|----------------|---------|
| **Autenticación** | Usuario/contraseña con `xpack.security.enabled=true` |
| **TLS en tránsito** | Certificados autofirmados generados automáticamente (CA propia) |
| **TLS en transporte** | Comunicación cifrada en la capa interna del clúster |
| **Credenciales por entorno** | Gestionadas mediante fichero `.env` (no hardcodeadas) |
| **Usuario separado** | `kibana_system` con permisos mínimos para Kibana |

> ⚠️ El fichero `.env` **no debe subirse a un repositorio público**. Está incluido en `.gitignore`.

---

## ⚠️ Problemas y retos encontrados

- El servicio `setup` debe completarse antes de que arranque Elasticsearch; se gestiona con `healthcheck` y `depends_on: condition: service_healthy`.
- La contraseña de `kibana_system` no se puede configurar por variable de entorno; el script `setup-passwords.sh` lo automatiza vía API REST.
- El campo `position` debe definirse como `geo_point` en el mapping **antes** de insertar el primer documento; si Elasticsearch lo infiere solo, lo trata como `object` y Kibana Maps no funciona.
- La memoria mínima para el stack completo es ~3-4 GB; se limita el heap de ES con `ES_JAVA_OPTS=-Xms512m -Xmx512m` y cada contenedor con `mem_limit: 1g`.

---

## 📈 Posibles vías de mejora

- **API real de tráfico aéreo** (OpenSky Network, ADS-B Exchange) vía Logstash o Filebeat para datos reales en lugar de simulados
- **Alertas en Kibana** (Watcher) que envíen notificaciones por email o Slack cuando `alert=true`
- **Clúster multi-nodo** con réplicas para alta disponibilidad y tolerancia a fallos
- **ILM (Index Lifecycle Management)** para rotar y archivar datos históricos automáticamente
- **Machine Learning** de Elastic para detección de anomalías en altitud o velocidad
- **APM** para monitorizar el rendimiento del propio generador de datos

---

## 🔄 Alternativas posibles

| Componente | Alternativa |
|------------|-------------|
| Elasticsearch | InfluxDB, TimescaleDB, OpenSearch |
| Kibana | Grafana, Metabase, Apache Superset |
| Python generator | Node-RED, Apache NiFi, Telegraf |
| Docker Compose | Kubernetes (Helm charts oficiales de Elastic) |

---

## 📁 Estructura del proyecto

```
elastic-iot/
├── docker-compose.yml          # Orquestación de los 4 servicios
├── .env                        # Variables de entorno (⚠️ no publicar)
├── .gitignore
├── README.md
├── data-generator/
│   ├── Dockerfile              # Imagen Python del generador
│   ├── requirements.txt        # elasticsearch==8.13.0
│   └── generator.py            # Generador de tráfico aéreo
├── setup/
│   └── setup-passwords.sh      # Configura kibana_system (ejecutar una vez)
└── dashboards/
    └── iot-dashboard-template.json   # Plantilla del dashboard de Kibana
```
