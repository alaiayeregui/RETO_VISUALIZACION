# 📡 colector-datos - Recolector de Datos de Tráfico

Script Python que obtiene datos de tráfico en tiempo real desde **TomTom API** y los envía a **Elasticsearch**.

## ✨ Características

✅ **Retry Logic**: Intenta conectarse a Elasticsearch hasta 12 veces con backoff exponencial  
✅ **Logs Claros**: Cada paso está documentado con prefijos `[CONEXIÓN]`, `[API]`, `[PROCESAMIENTO]`, etc.  
✅ **Validaciones**: Verifica que todas las variables de entorno estén configuradas  
✅ **Geolocalización**: Mapea coordenadas (lat/lon) con tipo `geo_point` para Kibana  
✅ **Gestión de Errores**: Maneja timeouts, errores HTTP y excepciones   
✅ **Logs en Tiempo Real**: PYTHONUNBUFFERED=1 para ver logs inmediatamente en `docker logs`  

## 📁 Archivos

- **main.py**: Script principal mejorado
- **requirements.txt**: Dependencias Python
- **Dockerfile**: Imagen Docker con PYTHONUNBUFFERED=1

## 🔧 Variables de Entorno

| Variable | Valor | Notas |
|----------|-------|-------|
| `TOMTOM_API_KEY` | `tu_clave_aqui` | **Obligatorio** - Obtén en https://developer.tomtom.com/ |
| `ELASTIC_HOST` | `http://elasticsearch:9200` | URL de Elasticsearch (en Docker: nombre del servicio) |
| `PYTHONUNBUFFERED` | `1` | Para logs en tiempo real |

## 🚀 Ejecución

### Con Docker Compose (recomendado)
```bash
docker-compose up -d
docker logs -f colector-datos
```

### Local (desarrollo)
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
export TOMTOM_API_KEY="tu_clave_aqui"
export ELASTIC_HOST="http://localhost:9200"

# Ejecutar
python main.py
```

## 📊 Flujo de Datos

```
1. Validar TOMTOM_API_KEY
2. Conectar a Elasticsearch (con reintentos)
3. Crear índice "traffic-history" con mapping geo_point
4. [BUCLE cada 5 minutos]
   ├─ Solicitar datos a TomTom API (BBOX Madrid)
   ├─ Procesar incidentes
   ├─ Indexar en Elasticsearch
   └─ Esperar 300 segundos
```

## 🎯 Datos Indexados

Cada incidente se indexa con:
```json
{
  "timestamp": "2024-05-12T19:30:45",
  "description": "Traffic accident",
  "severity": 1,
  "delay": 15,
  "location": {
    "lat": 40.41,
    "lon": -3.71
  },
  "type": 0
}
```

## 🐛 Debugging

Ver logs en tiempo real:
```bash
docker logs -f colector-datos
```

Ejemplos de logs esperados:
```
[INICIO] Sistema de recolección de tráfico iniciando...
[CONFIG] Cargando variables de entorno...
[CONFIG] ✅ TOMTOM_API_KEY configurada
[CONEXIÓN] Intento 1/12 de conectarse a http://elasticsearch:9200...
[CONEXIÓN] ✅ Conexión exitosa a Elasticsearch
[ÍNDICE] Creando índice 'traffic-history' con mapping...
[ÍNDICE] ✅ Índice 'traffic-history' creado exitosamente.
[SETUP] ✅ Setup completado correctamente
[CICLO 1] 2024-05-12 19:30:45
[API] 🌐 Solicitando datos a TomTom API...
[API] ✅ Respuesta recibida de TomTom
[PROCESAMIENTO] 📊 Encontrados 5 incidentes de tráfico
[PROCESAMIENTO] 🚀 19:30:45 - 5/5 incidencias indexadas en Elasticsearch.
```

## 🚨 Errores Comunes

### ❌ `TOMTOM_API_KEY no está configurada`
**Solución**: Edita `.env` con tu API key real

### ❌ `Intento X/12 falló: Connection refused`
**Causa**: Elasticsearch no está disponible  
**Solución**: Espera 40 segundos a que inicie Elasticsearch, o revisa `docker logs elasticsearch`

### ❌ `Error HTTP 401 - Unauthorized`
**Causa**: TOMTOM_API_KEY es inválida  
**Solución**: Verifica tu clave en https://developer.tomtom.com/

### ⚠️ `No hay incidencias activas en este momento`
**Cause**: No hay incidentes de tráfico en el área (BBOX Madrid)  
**Es Normal**: Puede ocurrir en horarios de bajo tráfico

## 🔄 Ciclo de Reintento

Si Elasticsearch no está disponible:
```
Intento 1 → Espera 5 segundos
Intento 2 → Espera 7.5 segundos
Intento 3 → Espera 11.25 segundos
...
Intento 12 → Espera 30 segundos (máximo)
```

Si falla tras 12 intentos → El contenedor se detiene

## 📝 Notas

- El script indexa **cada documento de forma individual** (no en batch)
- Usa **UTC** para timestamps
- **No elimina índices antiguos** (persisten en Elasticsearch)
- El ciclo es de **5 minutos** entre solicitudes (configurable)

---

**Última actualización**: Mayo 2024  
**Estado**: ✅ Funcional con retry logic, logs y validaciones
