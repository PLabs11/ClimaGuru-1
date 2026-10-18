"""
Servicio de Clima - ClimaGuru
==============================
Integración con múltiples APIs meteorológicas:
  - Meteoblue (pronóstico y modelos NMM)
  - Meteosource (clima actual y pronóstico)
  - IDEAM (datos históricos y estaciones oficiales Colombia via datos.gov.co y ERA5)
  - OpenWeatherMap (clima actual y pronóstico)
  - Open-Meteo (datos de modelos globales sin API key)
"""

import os
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def _get_env(key, default=''):
    return os.getenv(key, default)

def _get(url, params, timeout=12):
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("[WeatherService] Error GET %s: %s", url, e)
        return None


def _wind_dir_label(degrees):
    if degrees is None:
        return ''
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']
    idx = round(float(degrees) / 45) % 8
    return dirs[idx]


# Diccionario de ciudades comunes para geocodificación rápida
CIUDADES_COORDINATES = {
    'bogota': (4.7110, -74.0721),
    'bogotá': (4.7110, -74.0721),
    'medellin': (6.2442, -75.5812),
    'medellín': (6.2442, -75.5812),
    'cali': (3.4516, -76.5320),
    'barranquilla': (10.9685, -74.7813),
    'cartagena': (10.3910, -75.4794),
    'bucaramanga': (7.1254, -73.1198),
    'pereira': (4.8133, -75.6961),
    'santa marta': (11.2408, -74.1990),
    'cucuta': (7.8939, -72.5078),
    'cúcuta': (7.8939, -72.5078),
    'manizales': (5.0689, -75.5174),
    'ibague': (4.4389, -75.2322),
    'ibagué': (4.4389, -75.2322),
    'pasto': (1.2136, -77.2811),
    'villavicencio': (4.1420, -73.6266),
    'armenia': (4.5339, -75.6811),
    'neiva': (2.9273, -75.2819),
    'monteria': (8.7479, -75.8814),
    'montería': (8.7479, -75.8814),
    'popayan': (2.4448, -76.6147),
    'popayán': (2.4448, -76.6147),
    'valledupar': (10.4631, -73.2532),
    'tunja': (5.5353, -73.3678),
    'riohacha': (11.5444, -72.9072),
    'sincelejo': (9.3047, -75.3978),
    'florencia': (1.6144, -75.6062),
    'quibdo': (5.6919, -76.6583),
    'quibdó': (5.6919, -76.6583),
    'ciudad de mexico': (19.4326, -99.1332),
    'cdmx': (19.4326, -99.1332),
    'guadalajara': (20.6597, -103.3496),
    'monterrey': (25.6866, -100.3161),
    'lima': (-12.0464, -77.0428),
    'buenos aires': (-34.6037, -58.3816),
    'santiago': (-33.4489, -70.6693),
    'madrid': (40.4168, -3.7038),
}


def geocode_city(ciudad):
    """
    Convierte un nombre de ciudad a (latitud, longitud)
    """
    if not ciudad:
        return None, None
    norm = ciudad.strip().lower()
    if norm in CIUDADES_COORDINATES:
        return CIUDADES_COORDINATES[norm]

    # Geocodificación via OpenWeather
    ow_key = _get_env('OPENWEATHER_API_KEY', '')
    if ow_key:
        data = _get('http://api.openweathermap.org/geo/1.0/direct', {
            'q': ciudad, 'limit': 1, 'appid': ow_key
        })
        if data and len(data) > 0:
            return float(data[0].get('lat')), float(data[0].get('lon'))

    # Geocodificación via Open-Meteo
    data = _get('https://geocoding-api.open-meteo.com/v1/search', {
        'name': ciudad, 'count': 1
    })
    if data and data.get('results'):
        r = data['results'][0]
        return float(r.get('latitude')), float(r.get('longitude'))

    # Por defecto centro de Colombia si falla
    return 4.7110, -74.0721


# ==========================================
# 1. OPENWEATHERMAP
# ==========================================

def get_openweather_current(lat, lon):
    api_key = _get_env('OPENWEATHER_API_KEY', '')
    if not api_key:
        return None
    data = _get('https://api.openweathermap.org/data/2.5/weather', {
        'lat': lat, 'lon': lon,
        'appid': api_key,
        'units': 'metric', 'lang': 'es'
    })
    if not data:
        return None
    main = data.get('main', {})
    wind = data.get('wind', {})
    rain = data.get('rain', {})
    wlist = data.get('weather', [{}])
    desc = wlist[0].get('description', '') if wlist else ''
    return {
        'fuente': 'OpenWeatherMap',
        'temperatura': main.get('temp'),
        'temperatura_min': main.get('temp_min'),
        'temperatura_max': main.get('temp_max'),
        'humedad': main.get('humidity'),
        'presion': main.get('pressure'),
        'velocidad_viento': wind.get('speed'),
        'direccion_viento': wind.get('deg'),
        'nubosidad': data.get('clouds', {}).get('all'),
        'precipitacion': rain.get('1h', 0),
        'descripcion': desc.capitalize() if desc else 'Despejado',
        'ciudad': data.get('name'),
        'pais': data.get('sys', {}).get('country'),
        'visibilidad': data.get('visibility'),
        'raw': data
    }


def get_openweather_forecast(lat, lon, days=5):
    api_key = _get_env('OPENWEATHER_API_KEY', '')
    if not api_key:
        return None
    data = _get('https://api.openweathermap.org/data/2.5/forecast', {
        'lat': lat, 'lon': lon,
        'appid': api_key,
        'units': 'metric', 'lang': 'es',
        'cnt': days * 8
    })
    if not data:
        return None
    pronostico = []
    for item in data.get('list', []):
        main = item.get('main', {})
        wind = item.get('wind', {})
        wlist = item.get('weather', [{}])
        desc = wlist[0].get('description', '') if wlist else ''
        pronostico.append({
            'fecha': item.get('dt_txt'),
            'temperatura': main.get('temp'),
            'temperatura_min': main.get('temp_min'),
            'temperatura_max': main.get('temp_max'),
            'humedad': main.get('humidity'),
            'presion': main.get('pressure'),
            'velocidad_viento': wind.get('speed'),
            'descripcion': desc.capitalize() if desc else '',
        })
    return {
        'fuente': 'OpenWeatherMap',
        'ciudad': data.get('city', {}).get('name'),
        'pronostico': pronostico,
        'raw': data
    }


# ==========================================
# 2. METEOBLUE
# ==========================================

def get_meteoblue_forecast(lat, lon):
    api_key = _get_env('METEOBLUE_API_KEY', '0dvO2kqZSoiAmb7g')
    base_url = _get_env('METEOBLUE_BASE_URL', 'https://my.meteoblue.com')
    if not api_key:
        return None
    data = _get(base_url + '/packages/basic-day', {
        'lat': lat, 'lon': lon,
        'apikey': api_key,
        'asl': 0, 'temperature': 'C',
        'format': 'json'
    })
    if not data:
        return None
    d = data.get('data_day', {})
    tiempo     = d.get('time', [])
    temps_max  = d.get('temperature_max', [])
    temps_min  = d.get('temperature_min', [])
    precip     = d.get('precipitation', [])
    wind_speed = d.get('windspeed_mean', [])
    hums       = d.get('relativehumidity_mean', [])
    pronostico = []
    for i, t in enumerate(tiempo):
        pronostico.append({
            'fecha': t,
            'temperatura_max': temps_max[i] if i < len(temps_max) else None,
            'temperatura_min': temps_min[i] if i < len(temps_min) else None,
            'humedad': hums[i] if i < len(hums) else None,
            'precipitacion': precip[i] if i < len(precip) else None,
            'velocidad_viento': wind_speed[i] if i < len(wind_speed) else None,
            'descripcion': 'Modelo Meteoblue NMM'
        })
    return {'fuente': 'Meteoblue', 'pronostico': pronostico, 'raw': data}


def get_meteoblue_current(lat, lon):
    api_key = _get_env('METEOBLUE_API_KEY', '0dvO2kqZSoiAmb7g')
    base_url = _get_env('METEOBLUE_BASE_URL', 'https://my.meteoblue.com')
    if not api_key:
        return None
    data = _get(base_url + '/packages/basic-day', {
        'lat': lat, 'lon': lon,
        'apikey': api_key,
        'asl': 0, 'temperature': 'C',
        'format': 'json'
    })
    if not data:
        return None
    d = data.get('data_day', {})
    temps_instant = d.get('temperature_instant', [])
    temps_max = d.get('temperature_max', [])
    temps_min = d.get('temperature_min', [])
    hums = d.get('relativehumidity_mean', [])
    press = d.get('sealevelpressure_mean', [])
    winds = d.get('windspeed_mean', [])
    wdirs = d.get('winddirection', [])
    precips = d.get('precipitation', [])

    temp_now = temps_instant[0] if temps_instant else (temps_max[0] if temps_max else None)

    return {
        'fuente': 'Meteoblue',
        'temperatura': round(temp_now, 1) if temp_now is not None else None,
        'temperatura_min': temps_min[0] if temps_min else None,
        'temperatura_max': temps_max[0] if temps_max else None,
        'humedad': hums[0] if hums else None,
        'presion': press[0] if press else None,
        'velocidad_viento': winds[0] if winds else None,
        'direccion_viento': wdirs[0] if wdirs else None,
        'precipitacion': precips[0] if precips else 0,
        'descripcion': 'Modelo Meteorológico Meteoblue NMM (mLM)',
        'raw': data
    }


def get_meteoblue_nmm_dataset(lat, lon, domain="NMM18", asl=0, time_resolution="hourly"):
    """
    Consulta directa a la Dataset API de Meteoblue para modelos numéricos NMM / NEMS.
    
    Dominios soportados:
      - 'NMM18': Grilla regional meso-escalar para Suramérica (resolución de 18 km)
      - 'NEMSAUTO': Selección automática de la máxima resolución disponible (NEMS4, NEMS12, etc.)
      - 'NEMSGLOBAL': Modelo global multiescala de Meteoblue
    """
    api_key = _get_env('METEOSBLUE_API_KEY') or _get_env('METEOBLUE_API_KEY', '0dvO2kqZSoiAmb7g')
    base_url = _get_env('METEOBLUE_BASE_URL', 'https://my.meteoblue.com')
    if not api_key:
        return {'error': 'METEOBLUE_API_KEY no configurada'}

    url = f"{base_url}/dataset/query?apikey={api_key}"
    payload = {
        "units": {
            "temperature": "C",
            "velocity": "km/h",
            "precipitation": "mm"
        },
        "geometry": {
            "type": "MultiPoint",
            "coordinates": [[float(lon), float(lat), int(asl)]]
        },
        "queries": [
            {
                "domain": domain,
                "timeResolution": time_resolution,
                "codes": [
                    {"code": 11, "level": "2 m above gnd"},  # Temperatura
                    {"code": 32, "level": "10 m above gnd"}, # Velocidad viento
                    {"code": 61, "level": "surface"}         # Precipitación
                ]
            }
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        return {
            'fuente': f'Meteoblue Dataset API ({domain})',
            'dominio': domain,
            'resolucion': time_resolution,
            'coordenadas': {'lat': lat, 'lon': lon, 'asl': asl},
            'datos': data
        }
    except Exception as e:
        logger.warning("[WeatherService] Error consultando Meteoblue Dataset API (%s): %s", domain, e)
        return {
            'fuente': f'Meteoblue Dataset API ({domain})',
            'dominio': domain,
            'error': str(e),
            'aviso': 'La Dataset API requiere créditos o paquete de datos activo en my.meteoblue.com'
        }


# ==========================================
# 3. METEOSOURCE
# ==========================================

def get_meteosource_current(lat, lon):
    api_key = _get_env('METEOSOURCE_API_KEY', 'yhverrxl1iqgzypamd6rtv30uhxwlych29g1depb')
    base_url = _get_env('METEOSOURCE_BASE_URL', 'https://www.meteosource.com/api/v1/free')
    if not api_key:
        return None
    data = _get(base_url + '/point', {
        'lat': lat, 'lon': lon,
        'key': api_key,
        'sections': 'current',
        'language': 'en',
        'units': 'metric'
    })
    if not data:
        return None
    current = data.get('current', {})
    wind    = current.get('wind', {})
    return {
        'fuente': 'Meteosource',
        'temperatura': current.get('temperature'),
        'humedad': current.get('humidity'),
        'presion': current.get('pressure'),
        'velocidad_viento': wind.get('speed'),
        'direccion_viento': wind.get('angle'),
        'nubosidad': current.get('cloud_cover'),
        'precipitacion': current.get('precipitation', {}).get('total', 0),
        'descripcion': current.get('summary', 'Meteosource Machine Learning Model'),
        'raw': data
    }


def get_meteosource_forecast(lat, lon):
    api_key = _get_env('METEOSOURCE_API_KEY', 'yhverrxl1iqgzypamd6rtv30uhxwlych29g1depb')
    base_url = _get_env('METEOSOURCE_BASE_URL', 'https://www.meteosource.com/api/v1/free')
    if not api_key:
        return None
    data = _get(base_url + '/point', {
        'lat': lat, 'lon': lon,
        'key': api_key,
        'sections': 'daily',
        'language': 'en',
        'units': 'metric'
    })
    if not data:
        return None
    daily = data.get('daily', {}).get('data', [])
    pronostico = []
    for d in daily:
        all_day = d.get('all_day', {})
        pronostico.append({
            'fecha': d.get('day'),
            'temperatura_max': all_day.get('temperature_max'),
            'temperatura_min': all_day.get('temperature_min'),
            'humedad': all_day.get('humidity'),
            'precipitacion': all_day.get('precipitation', {}).get('total', 0),
            'velocidad_viento': all_day.get('wind', {}).get('speed'),
            'descripcion': all_day.get('summary', 'Meteosource'),
        })
    return {'fuente': 'Meteosource', 'pronostico': pronostico, 'raw': data}


# ==========================================
# 4. IDEAM (Datos Abiertos Colombia + ERA5)
# ==========================================

def get_ideam_stations_near(lat, lon, limit=5):
    """
    Consulta estaciones oficiales de monitoreo del IDEAM Colombia desde datos.gov.co
    Dataset sbwg-7ju4 (Temperatura del Aire - Red Nacional de Estaciones IDEAM)
    """
    try:
        url = 'https://www.datos.gov.co/resource/sbwg-7ju4.json'
        params = {'$limit': limit}
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            estaciones_raw = resp.json()
            estaciones = []
            for e in estaciones_raw:
                estaciones.append({
                    'codigo': e.get('codigoestacion'),
                    'nombre': e.get('nombreestacion', 'Estación IDEAM'),
                    'departamento': e.get('departamento', 'Colombia'),
                    'municipio': e.get('municipio', ''),
                    'temperatura_registrada': float(e.get('valorobservado')) if e.get('valorobservado') else None,
                    'fecha_observacion': e.get('fechaobservacion', ''),
                    'sensor': e.get('descripcionsensor', 'Temp Aire 2m'),
                    'fuente': 'IDEAM Colombia (datos.gov.co)'
                })
            return estaciones
    except Exception as e:
        logger.warning("[WeatherService] Error consultando estaciones IDEAM: %s", e)
    return []


def get_ideam_climate_data(lat, lon):
    """
    Obtiene historial de 7 días de reanálisis ERA5 de alta precisión (utilizado por IDEAM)
    y estaciones oficiales de la red nacional del IDEAM
    """
    # Consulta de historial climático usando Open-Meteo past_days=7
    data = _get('https://api.open-meteo.com/v1/forecast', {
        'latitude': lat,
        'longitude': lon,
        'past_days': 7,
        'forecast_days': 1,
        'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,windspeed_10m_max,relative_humidity_2m_mean',
        'timezone': 'America/Bogota'
    })
    
    estaciones = get_ideam_stations_near(lat, lon, limit=5)

    if not data:
        return {
            'fuente': 'IDEAM Oficial',
            'estaciones_ideam': estaciones,
            'historico_diario': []
        }

    daily  = data.get('daily', {})
    times  = daily.get('time', [])
    t_max  = daily.get('temperature_2m_max', [])
    t_min  = daily.get('temperature_2m_min', [])
    t_mean = daily.get('temperature_2m_mean', [])
    precip = daily.get('precipitation_sum', [])
    wind   = daily.get('windspeed_10m_max', [])
    hum    = daily.get('relative_humidity_2m_mean', [])

    historico = []
    for i, t in enumerate(times):
        historico.append({
            'fecha': t,
            'temperatura_max': t_max[i] if i < len(t_max) else None,
            'temperatura_min': t_min[i] if i < len(t_min) else None,
            'temperatura_media': t_mean[i] if i < len(t_mean) else None,
            'precipitacion': precip[i] if i < len(precip) else None,
            'velocidad_viento_max': wind[i] if i < len(wind) else None,
            'humedad_media': hum[i] if i < len(hum) else None,
            'fuente': 'IDEAM / ERA5 Reanálisis'
        })

    valid_temps  = [x for x in t_mean if x is not None]
    valid_precip = [x for x in precip if x is not None]
    valid_hum    = [x for x in hum if x is not None]

    return {
        'fuente': 'IDEAM / Open-Meteo ERA5',
        'estaciones_ideam': estaciones,
        'temperatura_media': round(sum(valid_temps) / len(valid_temps), 1) if valid_temps else None,
        'temperatura_min': min(t_min) if t_min else None,
        'temperatura_max': max(t_max) if t_max else None,
        'precipitacion_total': round(sum(valid_precip), 1) if valid_precip else 0,
        'humedad_media': round(sum(valid_hum) / len(valid_hum), 0) if valid_hum else None,
        'historico_diario': historico,
        'raw': data
    }


# ==========================================
# 5. OPEN-METEO GLOBAL
# ==========================================

def get_openmeteo_current(lat, lon):
    data = _get('https://api.open-meteo.com/v1/forecast', {
        'latitude': lat, 'longitude': lon,
        'current_weather': True,
        'hourly': 'relativehumidity_2m,surface_pressure,precipitation',
        'timezone': 'America/Bogota', 'forecast_days': 1
    })
    if not data:
        return None
    cw   = data.get('current_weather', {})
    hrly = data.get('hourly', {})
    hum  = hrly.get('relativehumidity_2m', [None])[0]
    pres = hrly.get('surface_pressure', [None])[0]
    prec = hrly.get('precipitation', [None])[0]
    return {
        'fuente': 'Open-Meteo',
        'temperatura': cw.get('temperature'),
        'humedad': hum,
        'presion': pres,
        'velocidad_viento': cw.get('windspeed'),
        'direccion_viento': cw.get('winddirection'),
        'precipitacion': prec,
        'descripcion': 'Modelo GFS/ICON (Open-Meteo)',
        'raw': data
    }


# ==========================================
# AGREGADOR MULTI-FUENTE
# ==========================================

def get_weather_aggregated(lat, lon, tipo='actual'):
    """
    Agrega datos meteorológicos de todas las fuentes:
    - Meteoblue
    - Meteosource
    - OpenWeatherMap
    - IDEAM (Colombia & ERA5)
    - Open-Meteo
    """
    fuentes_ok  = []
    fuentes_raw = {}

    if tipo == 'historico':
        ideam_data = get_ideam_climate_data(lat, lon)
        if ideam_data:
            fuentes_ok.append('IDEAM / ERA5')
            fuentes_raw['ideam'] = ideam_data
            return {
                'temperatura': ideam_data.get('temperatura_media'),
                'temperatura_min': ideam_data.get('temperatura_min'),
                'temperatura_max': ideam_data.get('temperatura_max'),
                'humedad': ideam_data.get('humedad_media'),
                'presion': 1013.2,
                'velocidad_viento': None,
                'direccion_viento': None,
                'precipitacion': ideam_data.get('precipitacion_total'),
                'descripcion': 'Historial 7 días IDEAM / ERA5 Reanálisis Climático',
                'fuentes': fuentes_ok,
                'fuentes_raw': fuentes_raw,
                'historico_diario': ideam_data.get('historico_diario', []),
                'estaciones_ideam': ideam_data.get('estaciones_ideam', [])
            }
        return {
            'temperatura': None, 'humedad': None, 'presion': None,
            'velocidad_viento': None, 'direccion_viento': None,
            'precipitacion': None, 'descripcion': 'Sin datos históricos disponibles',
            'fuentes': [], 'fuentes_raw': {}
        }

    if tipo == 'pronostico':
        mb  = get_meteoblue_forecast(lat, lon)
        ms  = get_meteosource_forecast(lat, lon)
        owm = get_openweather_forecast(lat, lon)
        if mb:  fuentes_ok.append('Meteoblue');   fuentes_raw['meteoblue']   = mb
        if ms:  fuentes_ok.append('Meteosource'); fuentes_raw['meteosource'] = ms
        if owm: fuentes_ok.append('OpenWeather'); fuentes_raw['openweather'] = owm

        # Priorizar el pronóstico con más detalle
        pronostico = []
        if ms and ms.get('pronostico'):
            pronostico = ms.get('pronostico')
        elif mb and mb.get('pronostico'):
            pronostico = mb.get('pronostico')
        elif owm and owm.get('pronostico'):
            pronostico = owm.get('pronostico')

        p0 = pronostico[0] if pronostico else {}
        temp = p0.get('temperatura') or p0.get('temperatura_max')
        return {
            'temperatura': temp,
            'temperatura_min': p0.get('temperatura_min'),
            'temperatura_max': p0.get('temperatura_max'),
            'humedad': p0.get('humedad'),
            'presion': p0.get('presion', 1013),
            'velocidad_viento': p0.get('velocidad_viento'),
            'direccion_viento': None,
            'precipitacion': p0.get('precipitacion', 0),
            'descripcion': 'Pronóstico - ' + (', '.join(fuentes_ok) or 'Sin fuentes'),
            'fuentes': fuentes_ok,
            'fuentes_raw': fuentes_raw,
            'pronostico': pronostico,
        }

    # --- tipo == 'actual' ---
    owm  = get_openweather_current(lat, lon)
    mb   = get_meteoblue_current(lat, lon)
    ms   = get_meteosource_current(lat, lon)
    omeo = get_openmeteo_current(lat, lon)

    # También incluir estaciones IDEAM para contexto local si estamos cerca de Colombia
    ideam_stations = []
    if -4.5 <= lat <= 13.5 and -82.0 <= lon <= -66.0:
        ideam_stations = get_ideam_stations_near(lat, lon, limit=3)
        if ideam_stations:
            fuentes_ok.append('IDEAM')
            fuentes_raw['ideam'] = {'estaciones': ideam_stations}

    if owm:  fuentes_ok.append('OpenWeatherMap'); fuentes_raw['openweather'] = owm
    if mb:   fuentes_ok.append('Meteoblue');      fuentes_raw['meteoblue']   = mb
    if ms:   fuentes_ok.append('Meteosource');    fuentes_raw['meteosource'] = ms
    if omeo: fuentes_ok.append('Open-Meteo');     fuentes_raw['openmeteo']   = omeo

    valid_temps = [s['temperatura'] for s in [owm, mb, ms, omeo]
                   if s and s.get('temperatura') is not None]
    temp_avg = round(sum(valid_temps) / len(valid_temps), 1) if valid_temps else None

    valid_hums = [s['humedad'] for s in [owm, mb, ms, omeo]
                  if s and s.get('humedad') is not None]
    hum_avg = round(sum(valid_hums) / len(valid_hums)) if valid_hums else None

    valid_press = [s['presion'] for s in [owm, mb, ms, omeo]
                   if s and s.get('presion') is not None]
    press_avg = round(sum(valid_press) / len(valid_press), 1) if valid_press else None

    valid_winds = [s['velocidad_viento'] for s in [owm, mb, ms, omeo]
                   if s and s.get('velocidad_viento') is not None]
    wind_avg = round(sum(valid_winds) / len(valid_winds), 1) if valid_winds else None

    primary = owm or ms or mb or omeo or {}
    wdir = primary.get('direccion_viento')

    return {
        'temperatura': temp_avg if temp_avg is not None else primary.get('temperatura'),
        'temperatura_min': primary.get('temperatura_min'),
        'temperatura_max': primary.get('temperatura_max'),
        'humedad': hum_avg if hum_avg is not None else primary.get('humedad'),
        'presion': press_avg if press_avg is not None else primary.get('presion'),
        'velocidad_viento': wind_avg if wind_avg is not None else primary.get('velocidad_viento'),
        'direccion_viento': wdir,
        'direccion_viento_label': _wind_dir_label(wdir if isinstance(wdir, (int, float)) else None),
        'precipitacion': primary.get('precipitacion', 0),
        'descripcion': primary.get('descripcion', 'Condiciones normales'),
        'ciudad': primary.get('ciudad'),
        'pais': primary.get('pais'),
        'fuentes': fuentes_ok,
        'fuentes_raw': fuentes_raw,
        'estaciones_ideam': ideam_stations
    }
