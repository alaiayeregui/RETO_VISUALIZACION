# 🔧 Cambios Realizados - Guía de Uso

## ✅ Problemas Corregidos

### 1. **PYTHONUNBUFFERED=1 en Dockerfile**
- Ahora los logs aparecen en tiempo real en `docker logs colector-datos`
- Anteriormente, los logs estaban en buffer y no se veían

### 2. **Retry Logic con Backoff Exponencial**
- El script ahora intenta conectarse a Elasticsearch hasta 12 veces
- Espera inicial: 5 segundos, con backoff exponencial (máx 30 segundos)
- Esto resuelve el problema de "timeout connection refused"

### 3. **Validación de Variables de Entorno**
- Ahora valida que `TOMTOM_API_KEY` esté configurada
- Si falta, el contenedor se detiene inmediatamente con un error claro
- Si `ELASTIC_HOST` no está definida, usa `http://elasticsearch:9200` por defecto

### 4. **Logs Detallados para Debugging**
Cada paso ahora muestra mensajes claros:
```
[CONFIG] Cargando variables de entorno...
[CONEXIÓN] Intento 1/12 de conectarse a http://elasticsearch:9200...
[ÍNDICE] Creando índice 'traffic-history' con mapping...
[API] 🌐 Solicitando datos a TomTom API...
[PROCESAMIENTO] 📊 Encontrados 5 incidentes de tráfico
[PROCESAMIENTO] 🚀 19:30:45 - 5/5 incidencias indexadas en Elasticsearch.
```

### 5. **docker-compose.yml Mejorado**
- **healthcheck** en Elasticsearch: verifica que está listo
- **depends_on con condition: service_healthy**: asegura que servicios arranquen en orden
- **ELASTIC_HOST** fijo en `http://elasticsearch:9200` (el nombre del servicio)
- **PYTHONUNBUFFERED=1** en las variables de entorno del contenedor
- **restart: on-failure:5** para reintentar ante fallos
- **Network explícita** para mejor control de comunicación entre servicios

---

## 🚀 Cómo Ejecutar

### 1. **Configura tu TOMTOM_API_KEY**
Abre el archivo `.env`:
```bash
TOMTOM_API_KEY=tu_api_key_real_aqui
ELASTIC_HOST=http://elasticsearch:9200
```

Obtén tu API gratuita en: https://developer.tomtom.com/

### 2. **Levanta los servicios**
```bash
docker-compose up -d
```

### 3. **Monitorea los logs**
```bash
# Para ver solo colector-datos
docker logs -f colector-datos

# Para ver todos los servicios
docker-compose logs -f

# Ver logs históricos
docker logs colector-datos | head -100
```

### 4. **Verifica en Kibana**
- Abre http://localhost:5601
- Ve a Management > Index Patterns
- Crea un patrón con `traffic-history`
- Visualiza los datos en Discover

### 5. **Detener servicios**
```bash
docker-compose down
docker-compose down -v  # (también elimina volúmenes)
```

---

## 🐛 Debugging - Qué significan los logs

| Log | Significado | Acción |
|-----|-------------|--------|
| `[CONEXIÓN] ✅ Conexión exitosa` | Elasticsearch está listo | ✅ OK |
| `[API] ✅ Respuesta recibida` | TomTom API respondió | ✅ OK |
| `[PROCESAMIENTO] 📊 Encontrados 0` | Sin incidentes de tráfico | Puede ser normal (fin de semana/noche) |
| `[ERROR] TOMTOM_API_KEY no está` | Falta la API key | Edita `.env` |
| `[CONEXIÓN] ❌ Intento 1/12 falló` | Elasticsearch no responde | Espera o revisa `docker logs elasticsearch` |
| `Timeout en la solicitud` | TomTom tardó > 10 segundos | Revisa conexión a internet |

---

## 🔍 Troubleshooting

### Los logs siguen vacíos
```bash
# Fuerza reconstrucción
docker-compose down
docker-compose up -d --build

# Verifica PYTHONUNBUFFERED
docker inspect colector-datos | grep PYTHONUNBUFFERED
```

### "Connection refused"
```bash
# Verifica que Elasticsearch esté corriendo
docker exec elasticsearch curl -s http://localhost:9200/_cluster/health

# Espera un poco más (Elasticsearch tarda ~40 segundos en iniciar)
docker logs elasticsearch | tail -20
```

### Índice no se crea
```bash
# Verifica si el índice existe
docker exec elasticsearch curl -s http://localhost:9200/_cat/indices

# Verifica la salud de Elasticsearch
docker exec elasticsearch curl -s http://localhost:9200/_cluster/health
```

---

## 📦 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `Dockerfile` | ✅ Agregado `PYTHONUNBUFFERED=1` |
| `main.py` | ✅ Retry logic, validaciones, logs claros |
| `docker-compose.yml` | ✅ healthcheck, depends_on, ELASTIC_HOST, restart policy, network |
| `.env` | ⚠️ Necesitas agregar tu TOMTOM_API_KEY |
| `.env.example` | ✨ Nuevo: ejemplo de configuración |

---

## 📝 Notas

- El script espera 300 segundos (5 minutos) entre ciclos
- Elasticsearch puede tardar 40-50 segundos en arrancar completamente
- Si no hay incidentes, verás ⚠️ "No hay incidencias activas" (es normal)
- Los datos se indexan con timestamp UTC
- El índice persiste en el volumen `es_data`

¡Listo! Ahora debería funcionar correctamente. 🎉
