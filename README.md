# 🏭 IoT Industrial — Visualización de Datos con Elastic Stack

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

Plataforma IoT industrial que simula una red de **8 plantas industriales distribuidas por el País Vasco**, cada una con múltiples máquinas y sensores. Los datos se indexan en tiempo real en Elasticsearch y se visualizan en Kibana, incluyendo un **mapa geográfico interactivo**.

### Arquitectura

```
┌─────────────────┐     HTTPS/TLS      ┌──────────────────────┐
│  Data Generator │ ─────────────────▶ │   Elasticsearch 8.x  │
│  (Python)       │                    │   + TLS + Auth        │
└─────────────────┘                    └──────────┬───────────┘
                                                   │
                                       ┌──────────▼───────────┐
                                       │       Kibana          │
                                       │  Dashboard + Mapas    │
                                       └──────────────────────┘
```

### Datos generados

Cada 5 segundos se generan lecturas de sensores para 8 plantas:

| Campo | Descripción |
|-------|-------------|
| `@timestamp` | Marca temporal UTC |
| `plant_id` / `plant_name` | Identificador y nombre de planta |
| `location` | Coordenadas GPS (`geo_point`) |
| `machine_id` / `machine_type` | Máquina origen |
| `sensor_type` | temperatura, presión, vibración, humedad, consumo |
| `value` / `unit` | Valor y unidad de medida |
| `status` | operativo / mantenimiento / alerta |
| `alert` | `true` si supera el umbral crítico |
| `shift` | Turno actual (mañana/tarde/noche) |

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
1. `setup` — genera certificados TLS autofirmados
2. `elasticsearch` — nodo único con seguridad activada
3. `kibana` — interfaz web
4. `data-generator` — empieza a enviar lecturas

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
2. Crear data view con patrón `iot-sensors*`
3. Campo de tiempo: `@timestamp`

### 6 — Crear el Dashboard con Mapa

#### Mapa geográfico de plantas
1. **Maps** → Create map
2. Add layer → **Documents** → selecciona `iot-sensors*`
3. Geospatial field: `location`
4. Tooltip fields: `plant_name`, `sensor_type`, `value`, `alert`
5. Style: colorear por `alert` (rojo = alerta, verde = normal)

#### Gráficos adicionales recomendados
- **Line chart** de `value` filtrado por `sensor_type: temperatura`
- **Bar chart** de alertas agrupadas por `plant_name`
- **Donut** de distribución por `sensor_type`
- **Data table** de las últimas alertas (`alert: true`)
- **Metric** con contador total de alertas

### 7 — Verificar Elasticsearch directamente

```bash
# Ver el cluster (desde fuera del contenedor)
curl -k -u elastic:ElasticIoT2024! https://localhost:9200

# Ver los últimos 5 documentos
curl -k -u elastic:ElasticIoT2024! \
  "https://localhost:9200/iot-sensors/_search?size=5&sort=@timestamp:desc&pretty"

# Contar alertas activas
curl -k -u elastic:ElasticIoT2024! \
  "https://localhost:9200/iot-sensors/_count?q=alert:true&pretty"
```

### 8 — Detener el stack

```bash
docker compose down          # mantiene los datos
docker compose down -v       # elimina también los volúmenes (reset completo)
```

---

## 🔒 Seguridad implementada

| Característica | Detalle |
|----------------|---------|
| **Autenticación** | Usuario/contraseña con `xpack.security.enabled=true` |
| **TLS en tránsito** | Certificados autofirmados generados automáticamente (CA propia) |
| **TLS en transporte** | Comunicación cifrada entre nodos del clúster |
| **Credenciales por entorno** | Gestionadas mediante fichero `.env` (no hardcodeadas) |
| **Usuario separado** | `kibana_system` con permisos mínimos para Kibana |

> ⚠️ El fichero `.env` **no debe subirse a un repositorio público**. Está incluido en `.gitignore`.

---

## 📈 Posibles vías de mejora

- **Logstash / Filebeat** para ingestión desde fuentes reales (PLC, MQTT, OPC-UA)
- **Alertas en Kibana** (Watcher) que envíen emails o notificaciones cuando `alert=true`
- **Clúster multi-nodo** con réplicas para alta disponibilidad
- **ILM (Index Lifecycle Management)** para rotar y archivar datos históricos
- **Machine Learning** de Elastic para detección de anomalías automática
- **APM** para monitorizar el propio generador de datos
- **Grafana** como alternativa/complemento a Kibana para dashboards

---

## ⚠️ Problemas y retos encontrados

- El servicio `setup` debe completarse antes de que arranque Elasticsearch; se gestiona con `healthcheck` y `depends_on`.
- La contraseña de `kibana_system` debe establecerse manualmente la primera vez (el script `setup-passwords.sh` lo automatiza).
- Los campos `geo_point` en Elasticsearch requieren el mapping correcto antes de insertar datos; de lo contrario Kibana no puede crear visualizaciones de mapa.
- La memoria mínima para el stack completo es ~3 GB; en sistemas con menos RAM hay que reducir el heap de ES con `ES_JAVA_OPTS`.

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
├── docker-compose.yml          # Orquestación de servicios
├── .env                        # Variables de entorno (⚠️ no publicar)
├── .gitignore
├── README.md
├── data-generator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── generator.py            # Generador de datos IoT
├── setup/
│   └── setup-passwords.sh      # Script de configuración inicial
└── dashboards/
    └── iot-dashboard-template.json
```
