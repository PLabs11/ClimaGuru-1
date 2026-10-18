# Reporte Técnico Comparativo: ClimaGuru Base vs. ClimaGuru Versión Mejorada

**Fecha de análisis:** 17 de Octubre de 2026  
**Repositorio Base:** `C:\Users\juanb\Downloads\ClimaGuru-main.zip`  
**Repositorio Mejorado Actual:** `c:\Users\juanb\OneDrive\Documents\GitHub\ClimaGuru`  

---

## 1. Resumen Ejecutivo de la Comparativa

| Métrica | Versión Base (`ClimaGuru-main`) | Versión Mejorada (Actual) | Variación |
| :--- | :--- | :--- | :--- |
| **Total de Archivos de Código** | 246 archivos | 273 archivos | **+27 archivos** |
| **Archivos Nuevos Creados** | - | 27 archivos | **+27** |
| **Archivos Modificados** | - | 23 archivos | **23 refactorizados** |
| **Archivos Sin Cambios** | - | 223 archivos | Idénticos |
| **Motor de Consulta Meteorológica** | **Simulado** (`datos_simulados`, mock estático) | **Real Multi-Fuente Agregado** (5 proveedores en vivo) | **Producción Real** |
| **Base de Datos MySQL** | Modelos desalineados con el esquema SQL | Sincronización 100%, campos encriptados y relaciones ORM | **Resuelto** |
| **Dashboard y Estadísticas** | Datos estáticos / mock frontend | Blueprint `/api/dashboard/stats` conectado a MySQL | **Nuevo Módulo** |
| **Integración Frontend-Backend** | Desconexión en endpoints y contratos JSON | Tipado TypeScript alineado, mapas interactivos y métricas en vivo | **Operativo al 100%** |

---

## 2. ¿Qué fue lo que se mejoró? (Mejoras Clave de Arquitectura)

### A. Eliminación de Respuestas Simuladas y Creación del Servicio Meteorológico Real
* **En la versión base:** El endpoint `/consultas/tiempo-real` tenía un comentario `# TODO: Aquí se integrarían los clientes de las APIs externas` y devolvía valores quemados (`temperatura: 24.5`, `humedad: 65`, etc.) con un tiempo simulado de 500 ms.
* **En la versión mejorada:** Se desarrolló `backend/app/services/weather_service.py` (590 líneas), un motor unificado que:
  1. Consulta en tiempo real a **Meteoblue**, **Meteosource**, **OpenWeatherMap**, **Open-Meteo** y la red de estaciones oficiales del **IDEAM Colombia (datos.gov.co)** junto con reanálisis **ERA5**.
  2. Implementa un agregador inteligente (`get_weather_aggregated`) que promedia variables entre fuentes activas y calcula métricas ponderadas.
  3. Proporciona geocodificación automática local (ciudades principales de Colombia y Latinoamérica) y fallback a geocodificadores externos.
  4. Persiste automáticamente los registros meteorológicos en la tabla `datos_clima` asociada a la consulta en MySQL.

### B. Corrección Crítica del Modelo `APIKey` y Seguridad
* **En la versión base:** El modelo `APIKey` en `backend/app/models/api_key.py` utilizaba nombres de columnas incorrectos (`servicio_nombre`, `api_key` con longitud limitada a 255 caracteres que truncaba datos cifrados, `fecha_registro`). No tenía soporte para API Secret (necesario para firmar solicitudes HMAC en Meteoblue).
* **En la versión mejorada:**
  - Se mapeó exactamente a las columnas reales de MySQL: `proveedor`, `api_key_encrypted` (`Text`), `api_secret_encrypted`, `descripcion`, `activa`, `limite_consultas_diarias`, `consultas_realizadas`, `ultimo_uso`, `creada_en`, `actualizada_en`.
  - Se añadieron sinónimos de SQLAlchemy (`synonym`) para compatibilidad retroactiva.
  - Se implementó derivación segura de claves Fernet con `base64.urlsafe_b64encode` a 32 bytes para prevenir excepciones de inicialización.

### C. Módulo de Dashboard Analítico en Tiempo Real
* **En la versión base:** No existía API de dashboard. El frontend mostraba valores estáticos inventados.
* **En la versión mejorada:** Se creó `backend/app/routes/dashboard.py` con el endpoint `/api/dashboard/stats`, que calcula:
  - Total de consultas y consultas del día filtradas por usuario.
  - Conteo de API Keys activas en tiempo real.
  - Top 5 de ciudades más consultadas.
  - Serie temporal de consultas de los últimos 7 días.
  - Promedios históricos de temperatura, humedad, presión y viento almacenados en MySQL.

### D. Refactorización Profunda del Frontend (Next.js 14 / TypeScript)
* **Gestión de API Keys (`app/dashboard/api-keys/page.tsx`):** Ahora incluye un catálogo visual de proveedores (Meteoblue, Meteosource, OpenWeatherMap, WeatherAPI, etc.), enlaces oficiales a portales de desarrolladores, estado de encriptación, validación de formularios y eliminación/modificación con sincronización en MySQL.
* **Mapa Interactivo (`app/dashboard/mapa/page.tsx`):** Permite hacer clic en cualquier punto geográfico o buscar por nombre de ciudad; ejecuta la consulta multi-fuente en vivo; presenta tarjetas estilizadas con iconos dinámicos y genera la tabla de pronóstico extendido de 5 a 7 días.
* **Historial de Consultas (`app/dashboard/historial/page.tsx`):** Soporta acordeones desplegables con detalle de cada fuente utilizada, métricas climáticas completas, badges de estado y filtros de búsqueda instantáneos por ciudad o proveedor.
* **Soporte de Autenticación JWT:** Normalización de `identity` en tokens como `string` para cumplir con las últimas versiones de `flask_jwt_extended`, y adición del alias de ruta `/register` para compatibilidad internacional.

### E. Robustez en Entornos Windows y Manejo de Dependencias
* **Codificación UTF-8:** En `main.py` se implementó la reconfiguración automática de `sys.stdout` y `sys.stderr` a UTF-8 para prevenir errores `UnicodeEncodeError` comunes en la consola de Windows al imprimir emojis meteorológicos.
* **Importaciones Condicionales:** Las librerías científicas de radar (`Py-ART`, `Cartopy`) se protegieron con bloques `try...except`, permitiendo que el sistema funcione fluidamente incluso en entornos donde los binarios de radar de C/Fortran no estén instalados.

---

## 3. Detalle de Archivos y Líneas de Código Modificadas

A continuación se detalla la auditoría línea por línea de los archivos modificados entre ambas versiones:

### 3.1 Backend

#### `backend/app/services/weather_service.py`
* **Líneas previas:** 1 línea (placeholder vacío `# Weather service`).
* **Líneas nuevas:** 590 líneas.
* **Líneas añadidas:** `+589` | **Líneas eliminadas:** `-1`.
* **Cambios:**
  - **Líneas 1-38:** Helpers de entorno `_get_env`, cliente HTTP `_get` con timeout de 12s, y conversor de grados angulares a rosa de los vientos (`_wind_dir_label`).
  - **Líneas 40-112:** Diccionario `CIUDADES_COORDINATES` con más de 30 ciudades colombianas e internacionales, y función `geocode_city()` con fallback a OpenWeather y Open-Meteo Geocoding.
  - **Líneas 118-187:** Integración con OpenWeatherMap (`get_openweather_current`, `get_openweather_forecast`).
  - **Líneas 193-265:** Integración con Meteoblue (`get_meteoblue_current`, `get_meteoblue_forecast`) consumiendo `/packages/basic-day`.
  - **Líneas 271-329:** Integración con Meteosource (`get_meteosource_current`, `get_meteosource_forecast`) consumiendo `/point`.
  - **Líneas 335-425:** Integración con el dataset oficial del IDEAM en `datos.gov.co` (`get_ideam_stations_near`) y reanálisis climático ERA5 de alta resolución de 7 días (`get_ideam_climate_data`).
  - **Líneas 431-456:** Integración con Open-Meteo Global (`get_openmeteo_current`).
  - **Líneas 462-590:** Motor agregador unificado `get_weather_aggregated()` que fusiona, normaliza y promedia variables para los modos `actual`, `pronostico` e `historico`.

#### `backend/app/routes/consultas.py`
* **Líneas previas:** 350 líneas | **Líneas nuevas:** 414 líneas.
* **Líneas añadidas:** `+176` | **Líneas eliminadas:** `-112`.
* **Líneas cambiadas:**
  - **Líneas 18-24:** Importación de `time`, `get_weather_aggregated` y `geocode_city`. Inclusión de alias de ruta `@consultas_bp.route('', methods=['POST'])` y `@consultas_bp.route('/', methods=['POST'])`.
  - **Líneas 30-66:** Lógica de geocodificación previa a la consulta y normalización del tipo (`actual`, `pronostico`, `historico`).
  - **Líneas 68-84:** Creación de registro inicial de `Consulta` en estado `procesando` en MySQL.
  - **Líneas 85-115:** Llamada al servicio meteorológico real `get_weather_aggregated()`, instanciación de `DatosClima`, cálculo real del tiempo de respuesta (`time.time() - t0`) y transición a estado `completada`.
  - **Líneas 133-165:** Estructuración de respuesta JSON con métricas detalladas (`temperatura_min`, `temperatura_max`, `fuentes_lista`, `pronostico`, `historico_diario`, etc.) para el frontend.

#### `backend/app/models/consulta.py`
* **Líneas previas:** 61 líneas | **Líneas nuevas:** 88 líneas.
* **Líneas añadidas:** `+30` | **Líneas eliminadas:** `-3`.
* **Líneas cambiadas:**
  - **Línea 17:** Adición de `'actual'` a la definición de `Enum` del campo `tipo_consulta`.
  - **Líneas 38-39:** Definición explícita de la relación ORM:
    `datos_clima = db.relationship('DatosClima', backref='consulta', uselist=False, cascade='all, delete-orphan', lazy='joined')`.
  - **Líneas 61-85:** Método `to_dict()` ampliado para serializar recursivamente los datos climáticos adjuntos (`temperatura`, `humedad`, `presion`, `viento_vel`, `fuentes`, etc.), evitando consultas N+1 en SQLAlchemy.

#### `backend/app/models/api_key.py`
* **Líneas previas:** 112 líneas | **Líneas nuevas:** 108 líneas.
* **Líneas añadidas:** `+72` | **Líneas eliminadas:** `-76`.
* **Líneas cambiadas:**
  - **Líneas 18-35:** Reescritura completa de los atributos del modelo para coincidir con la tabla MySQL: `proveedor`, `api_key_encrypted`, `api_secret_encrypted`, `descripcion`, `limite_consultas_diarias`, `consultas_realizadas`, `ultimo_uso`. Inclusión de `synonym('proveedor')` para `servicio_nombre`.
  - **Líneas 65-79:** Métodos `set_api_secret()` y `get_api_secret()` con cifrado Fernet para soportar firmas criptográficas de Meteoblue.
  - **Líneas 81-86:** Método estático `_get_cipher()` con codificación base64 url-safe uniforme.
  - **Líneas 87-105:** Método `to_dict()` con generación de máscara de clave (`api_key_preview`: `4...4`).

#### `backend/app/routes/api_keys.py`
* **Líneas previas:** 231 líneas | **Líneas nuevas:** 204 líneas.
* **Líneas añadidas:** `+52` | **Líneas eliminadas:** `-79`.
* **Líneas cambiadas:**
  - **Líneas 19-25:** Función `get_cipher()` unificada.
  - **Líneas 28-42:** Corrección en `get_api_keys()` para filtrar por `usuario_id` sin colisiones de nombres de columna.
  - **Líneas 44-96:** Adaptación de `create_api_key()` para recibir tanto `proveedor` como `servicio_nombre`, validando duplicados y cifrando antes de persistir en base de datos.

#### `backend/app/routes/auth.py`
* **Líneas previas:** 290 líneas | **Líneas nuevas:** 301 líneas.
* **Líneas añadidas:** `+24` | **Líneas eliminadas:** `-13`.
* **Líneas cambiadas:**
  - **Línea 49:** Inclusión del alias `@auth_bp.route('/register', methods=['POST'])`.
  - **Líneas 107-108:** Conversión de identidad a string en generación de tokens:
    `access_token = create_access_token(identity=str(nuevo_usuario.id))` y `refresh_token = create_refresh_token(identity=str(nuevo_usuario.id))`.
  - **Líneas 115-121:** Inclusión de claves duales en respuesta (`'usuario'` y `'user'`).
  - **Líneas 144-150:** Normalización en login para aceptar `username_or_email`, `username` o `email` indistintamente.

#### `backend/app/routes/datos.py`
* **Líneas previas:** 14 líneas (archivo esqueleto).
* **Líneas nuevas:** 63 líneas.
* **Líneas añadidas:** `+56` | **Líneas eliminadas:** `-7`.
* **Líneas cambiadas:**
  - **Líneas 17-63:** Implementación completa del endpoint `GET /datos/historicos` con:
    - Verificación opcional de token JWT (`verify_jwt_in_request(optional=True)`).
    - Paginación (`page`, `per_page` con límite máximo de 100).
    - Filtro por nombre de ciudad (`Consulta.ciudad.ilike(...)`).
    - Join entre `DatosClima` y `Consulta` ordenado descendentemente por fecha.

#### `backend/app/__init__.py` y `backend/app/routes/__init__.py`
* **Líneas añadidas:** `+2` / `-1` en cada archivo.
* **Cambios:** Importación y registro del blueprint `dashboard_bp` con el prefijo `/api/dashboard`.

#### `backend/app/database.py`
* **Líneas cambiadas:** 200-204 (5 líneas modificadas).
* **Cambios:** Tratamiento seguro de logs al inspeccionar el esquema de tablas existentes y tablas faltantes.

---

### 3.2 Frontend

#### `frontend/app/dashboard/api-keys/page.tsx`
* **Líneas previas:** 290 líneas | **Líneas nuevas:** 533 líneas.
* **Líneas añadidas:** `+400` | **Líneas eliminadas:** `-157`.
* **Cambios:**
  - **Líneas 35-78:** Matriz de configuración de proveedores (`PROVIDERS`) con metadatos de Meteoblue, Meteosource, OpenWeatherMap, WeatherAPI, Visual Crossing.
  - **Líneas 80-110:** Claves de demostración de contingencia si el backend está en proceso de arranque.
  - **Líneas 120-220:** Manejo reactivo de estado para inserción y visualización (mostrar/ocultar texto de claves con iconos `Eye`/`EyeOff`).
  - **Líneas 230-530:** Interfaz rediseñada en tarjetas Shadcn/UI con badges temáticos de colores por API y validación en vivo.

#### `frontend/app/dashboard/mapa/page.tsx`
* **Líneas previas:** 243 líneas | **Líneas nuevas:** 526 líneas.
* **Líneas añadidas:** `+364` | **Líneas eliminadas:** `-81`.
* **Cambios:**
  - **Líneas 37-90:** Tipos TypeScript `WeatherResult` y controlador de envío compatible con coordenadas de clic del mapa o nombre de ciudad.
  - **Líneas 220-482:** Renderizado condicional de métricas climáticas avanzadas (temperatura actual, máxima, mínima, humedad, presión en hPa, velocidad del viento en km/h, dirección y precipitación).
  - **Líneas 484-526:** Tabla interactiva de pronóstico extendido a 7 días y panel de estaciones de monitoreo del IDEAM Colombia.

#### `frontend/app/dashboard/historial/page.tsx`
* **Líneas previas:** 316 líneas | **Líneas nuevas:** 449 líneas.
* **Líneas añadidas:** `+307` | **Líneas eliminadas:** `-174`.
* **Cambios:**
  - **Líneas 48-65:** Carga asíncrona de hasta 50 consultas con auto-expansión del primer registro.
  - **Líneas 70-98:** Filtro reactivo en tiempo real por término de búsqueda (ciudad, tipo o proveedor).
  - **Líneas 159-431:** Vista detallada tipo acordeón que expone los datos meteorológicos crudos y estructurados almacenados en MySQL.

#### `frontend/app/dashboard/page.tsx`
* **Líneas previas:** 282 líneas | **Líneas nuevas:** 317 líneas.
* **Líneas añadidas:** `+43` | **Líneas eliminadas:** `-8`.
* **Cambios:** Conexión del tablero principal al endpoint real `/api/dashboard/stats`, renderizando métricas dinámicas de uso, distribución de ciudades consultadas y promedios reales.

#### `frontend/app/login/page.tsx`
* **Líneas previas:** 144 líneas | **Líneas nuevas:** 194 líneas.
* **Líneas añadidas:** `+82` | **Líneas eliminadas:** `-32`.
* **Cambios:** Manejo de autenticación dual (redirección y almacenamiento seguro en cookies/localStorage del token JWT), interfaz con feedback de errores y selector de modo demo.

#### `frontend/lib/types.ts`
* **Líneas previas:** 83 líneas | **Líneas nuevas:** 119 líneas.
* **Líneas añadidas:** `+36`.
* **Cambios:** Definición de interfaces TypeScript para `DatosClima`, `WeatherResponse`, `DashboardStats` y metadatos de geolocalización.

---

### 3.3 Raíz y Scripts de Invocación

#### `main.py`
* **Líneas previas:** 457 líneas | **Líneas nuevas:** 472 líneas.
* **Líneas añadidas:** `+20` | **Líneas eliminadas:** `-5`.
* **Cambios:**
  - **Líneas 23-30:** Reconfiguración de `sys.stdout` y `sys.stderr` a `utf-8` para entornos Windows.
  - **Líneas 40-45:** Carga condicional resiliente de `IDEAMRadarDownloader` y `RadarDataProcessor`.
  - **Líneas 116-121:** Manejo de excepciones en la instanciación de Meteosource y validación de variables de entorno.

---

## 4. Análisis: ¿Se puede aplicar Semantic Kernel, LangChain o LangGraph? ¿Es útil?

### 4.1 Factibilidad Técnica
**Sí, es totalmente aplicable y de alto impacto.** ClimaGuru cuenta con múltiples fuentes de datos estructurados (JSON, DataFrames de pandas, series temporales, coordenadas) y no estructurados (boletines oficiales de alerta del IDEAM, alertas del SIATA, resúmenes meteorológicos).

### 4.2 Comparativa de Opciones

| Framework | Idoneidad para ClimaGuru | ¿Por qué y para qué? | Complejidad de Adopción |
| :--- | :--- | :--- | :--- |
| **LangGraph** *(Recomendado)* | **Excelente (10/10)** | Ideal para flujos cíclicos, orquestación de agentes con estado y resolución de discrepancias entre modelos meteorológicos (ej. debate entre GFS vs ECMWF). | Media |
| **LangChain** | **Muy Buena (8.5/10)** | Excelente para crear un Agente Meteorológico con herramientas (*Tool Calling*) y un sistema RAG sobre boletines y documentos del IDEAM/SIATA. | Baja - Media |
| **Semantic Kernel** | **Buena (7.5/10)** | Muy potente si el backend migrara a .NET o si se utiliza Azure OpenAI con conectores nativos de memoria de Microsoft. En un stack puramente Python/Flask, LangGraph y LangChain ofrecen un ecosistema mucho más ágil. | Media - Alta |

### 4.3 ¿Es útil? Casos de Uso Concretos para ClimaGuru

1. **Agente Meteorológico Consultivo ("ClimaGuru Copilot"):**
   - El usuario escribe en lenguaje natural: *"¿Habrá riesgo de inundación mañana en la Comuna 13 de Medellín para coordinar entrega de camiones?"*
   - LangChain/LangGraph invoca las herramientas existentes: `get_weather_aggregated()`, consulta radares del SIATA y estaciones del IDEAM.
   - Interpreta los datos numéricos y responde un análisis de riesgo en lenguaje natural.

2. **Resolución de Conflictos Multi-Modelo (Orquestación con LangGraph):**
   - Si Meteoblue predice 5 mm de lluvia y Meteosource predice 40 mm (tormenta severa), un grafo cíclico de LangGraph puede contrastar con el radar local del SIATA y reanálisis ERA5 para emitir una predicción sintetizada con nivel de confianza (*Confidence Score*).

3. **Generación Automática de Alertas Tempranas para Agro e Industria:**
   - Monitoreo periódico en segundo plano que analiza pronósticos de heladas, olas de calor o vientos fuertes, redactando alertas automáticas enviadas por correo o webhook.

---

## 5. Modelos NMM de Meteoblue: ¿Se están usando y cómo usarlos en el código?

### 5.1 ¿Se están usando actualmente?
* En `backend/app/services/weather_service.py` (líneas 222 y 262), el código asigna como etiqueta descriptiva: `'descripcion': 'Modelo Meteorológico Meteoblue NMM'`.
* **Sin embargo, a nivel de API:** Se está consumiendo el endpoint:
  ```http
  GET https://my.meteoblue.com/packages/basic-day?lat={lat}&lon={lon}&apikey={api_key}...
  ```
* En la infraestructura oficial de Meteoblue, el paquete `basic-day` **no** entrega el modelo NMM puro sin procesar; entrega su tecnología de consenso denominada **mLM (Learning MultiModel)**, que combina modelos globales (ECMWF, GFS, ICON) con ajustes estadísticos locales.
* La familia original **NMM** (*Nonhydrostatic Meso-Scale Modelling*, como NMM4, NMM12 y NMM18 para Suramérica) fue la tecnología pionera de Meteoblue y ha evolucionado hacia la arquitectura **NEMS** (*NOAA Environmental Modeling System*).

### 5.2 ¿Cómo usar los modelos NMM / NEMS directamente en el código?

Para consultar los modelos numéricos de alta resolución de Meteoblue de forma directa, se debe utilizar la **Dataset API** o solicitar paquetes avanzados especificando el dominio (`domain`):

#### Opción A: Consulta Directa de Dominio NMM/NEMS mediante JSON POST (Dataset API)
```python
import requests
import json

def get_meteoblue_raw_nmm(lat: float, lon: float, api_key: str):
    """
    Consulta directa de grillas de modelos NMM / NEMS de Meteoblue
    Dominio 'NMM18' para Suramérica o 'NEMSAUTO' para la máxima resolución local.
    """
    url = f"https://my.meteoblue.com/dataset/query?apikey={api_key}"
    
    payload = {
        "units": {
            "temperature": "C",
            "velocity": "km/h"
        },
        "geometry": {
            "type": "MultiPoint",
            "coordinates": [[lon, lat, 0]]
        },
        "queries": [
            {
                # "NMM18" para grilla NMM regional o "NEMSAUTO" para selección óptima
                "domain": "NEMSAUTO", 
                "timeResolution": "hourly",
                "codes": [
                    {"code": 11, "level": "2 m above gnd"},  # Temperatura 2m
                    {"code": 32, "level": "10 m above gnd"}, # Velocidad viento
                    {"code": 61, "level": "surface"}         # Precipitación acumulada
                ]
            }
        ]
    }
    
    resp = requests.post(url, json=payload, timeout=12)
    resp.raise_for_status()
    return resp.json()
```

#### Opción B: Paquete de Multi-Modelos Numéricos en la API Forecast
Si se dispone de suscripción con paquetes de modelos, se puede solicitar `packages/modelforecast-multimodel`:
```python
def get_meteoblue_multimodel_package(lat: float, lon: float, api_key: str):
    url = "https://my.meteoblue.com/packages/modelforecast-multimodel"
    params = {
        'lat': lat,
        'lon': lon,
        'apikey': api_key,
        'format': 'json'
    }
    resp = requests.get(url, params=params, timeout=12)
    return resp.json()
```

---

## 6. Meteosource Machine Learning: ¿Se está usando y cómo funciona?

### 6.1 ¿Se está usando en el código actual?
* **Sí, está activamente integrado y consultado.**
  - En `backend/app/services/weather_service.py` (líneas 271-329) y en `src/data_sources/Meteosource.py`.
  - Se consume el endpoint:
    ```http
    GET https://www.meteosource.com/api/v1/free/point?lat={lat}&lon={lon}&key={key}&sections=all
    ```
* **¿Se está usando su Machine Learning?**
  - **Sí.** El valor fundamental de Meteosource radica en que **todos sus endpoints procesan las previsiones mediante Machine Learning de forma nativa en su servidor**.
  - Meteosource no opera como un simple pasamanos de modelos; su backend ejecuta algoritmos de aprendizaje automático que ingieren modelos globales (ECMWF, GFS, ICON, GEM, UKMO), eliminan sesgos locales (*bias correction*) y generan una predicción combinada optimizada para las coordenadas específicas.

### 6.2 ¿Por qué no hay un parámetro `model="machine_learning"`?
En la API REST de Meteosource **no existe un parámetro URL para "activar" o "desactivar" el Machine Learning**. El pipeline de IA se ejecuta automáticamente del lado del servidor para cualquier petición a `/point`.

### 6.3 ¿Cómo aprovechar las funciones avanzadas de IA de Meteosource?

Si se cuenta con una clave de nivel superior (`Flexi` o `Premium`), se pueden desbloquear capacidades de IA avanzadas:

#### A. Nowcasting de Precipitación Minuto a Minuto con IA (`sections=minutely`)
Meteosource aplica algoritmos de aprendizaje sobre radares satelitales para predecir lluvia en intervalos de 1 minuto para las próximas 2 horas:

```python
def get_meteosource_ai_nowcasting(lat: float, lon: float, api_key: str):
    """
    Nowcasting de precipitación minuto a minuto optimizado por IA
    (Disponible en tiers Flexi/Premium de Meteosource)
    """
    url = "https://www.meteosource.com/api/v1/flexi/point"
    params = {
        'lat': lat,
        'lon': lon,
        'key': api_key,
        'sections': 'current,minutely,alerts',
        'language': 'es',
        'units': 'metric'
    }
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data.get('minutely', {})
    return None
```

#### B. Algoritmo de Predicción de Energía Solar y Eólica (Machine Learning Especializado)
Meteosource ofrece endpoints dedicados donde sus modelos de Machine Learning transforman la radiación solar difusa/directa y el cizallamiento del viento en estimaciones de generación energética en kilovatios:

```python
def get_meteosource_solar_ml(lat: float, lon: float, api_key: str, panel_kwp: float = 10.0):
    """
    Predicción de generación fotovoltaica calculada por algoritmos de ML de Meteosource
    """
    url = "https://www.meteosource.com/api/v1/flexi/solar"
    params = {
        'lat': lat,
        'lon': lon,
        'key': api_key,
        'system_capacity': panel_kwp
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json() if resp.status_code == 200 else None
```

---

## 7. Conclusiones y Próximos Pasos Recomendados

1. **La versión mejorada actual representa un salto cualitativo definitivo:** Pasó de ser un prototipo con datos mock y problemas de esquema en MySQL a una plataforma meteorológica unificada, resiliente y conectada con APIs internacionales y datos oficiales del IDEAM Colombia.
2. **Para la integración de IA (LangGraph/LangChain):** Se recomienda crear un sub-módulo `backend/app/ai/weather_agent.py` usando LangGraph para análisis contextual y generación de alertas automáticas.
3. **Para Meteoblue NMM:** Añadir el método de Dataset API (`NEMSAUTO`/`NMM18`) en `src/data_sources/meteoblue.py` para usuarios que requieran matrices numéricas puras de meso-escala.
4. **Para Meteosource:** La integración actual ya aprovecha su tecnología de Machine Learning en el tier gratuito; habilitar el parámetro `sections=minutely` si se migra al tier Flexi/Premium para detección inmediata de lluvias.
