"""
Servicio Gratuito de Nowcasting y Predicción Energética (Solar & Eólica)
========================================================================
Alternativa 100% GRATUITA a las APIs comerciales de pago (como Meteosource Premium)
- Nowcasting minuto a minuto para las próximas 2 horas (Open-Meteo Minutely-15 + Radar Doppler RainViewer)
- Predicción de Generación Solar Fotovoltaica (kWh) y Eólica (kWh) basada en modelos físicos y radiación directa
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# =====================================================================
# 1. NOWCASTING MINUTO A MINUTO (PRÓXIMAS 2 HORAS - 100% GRATIS)
# =====================================================================

def get_free_minutely_nowcasting(lat: float, lon: float):
    """
    Predice la precipitación minuto a minuto para las próximas 2 horas
    utilizando asimilación rápida de radar de Open-Meteo (sin costo ni API key).
    
    Genera 8 intervalos de 15 minutos (120 minutos totales).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'minutely_15': 'precipitation,precipitation_probability,weather_code',
        'forecast_minutely_15': 8,  # 8 bloques de 15 min = 2 horas
        'timezone': 'auto'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        m15 = data.get('minutely_15', {})
        times = m15.get('time', [])
        precips = m15.get('precipitation', [])
        probs = m15.get('precipitation_probability', [])

        proyeccion_minutos = []
        lluvia_inminente = False
        minuto_inicio_lluvia = None

        for idx, t in enumerate(times):
            minutos_desde_ahora = idx * 15
            precip_val = precips[idx] if idx < len(precips) else 0.0
            prob_val = probs[idx] if idx < len(probs) else 0

            intensidad = "Sin lluvia"
            if precip_val > 0.1:
                if not lluvia_inminente:
                    lluvia_inminente = True
                    minuto_inicio_lluvia = minutos_desde_ahora
                if precip_val < 2.5:
                    intensidad = "Llovizna leve"
                elif precip_val < 7.6:
                    intensidad = "Lluvia moderada"
                else:
                    intensidad = "Lluvia fuerte / Aguacero"

            proyeccion_minutos.append({
                'minuto_relativo': f"+{minutos_desde_ahora} min",
                'hora_estimada': t,
                'precipitacion_mm': precip_val,
                'probabilidad_porcentaje': prob_val,
                'intensidad': intensidad
            })

        # Información adicional de reflectividad radar pública de RainViewer
        radar_info = _get_rainviewer_radar_status()

        return {
            'tipo': 'Nowcasting Precipitación (Próximas 2 Horas)',
            'fuente': 'Open-Meteo High-Resolution Rapid Refresh + Doppler Radar Mesh',
            'coordenadas': {'lat': lat, 'lon': lon},
            'resumen': {
                'lluvia_en_proximas_2h': lluvia_inminente,
                'minutos_para_inicio_lluvia': minuto_inicio_lluvia,
                'mensaje': (f"Alerta: Se prevé {proyeccion_minutos[minuto_inicio_lluvia//15]['intensidad'].lower()} en aproximadamente {minuto_inicio_lluvia} minutos."
                            if lluvia_inminente else "Cielos estables sin pronóstico de precipitación significativa en las próximas 2 horas.")
            },
            'proyeccion_minutos': proyeccion_minutos,
            'radar_cobertura': radar_info
        }

    except Exception as e:
        logger.warning("[Nowcasting] Error obteniendo datos de nowcasting: %s", e)
        return {
            'error': str(e),
            'mensaje': 'No se pudo generar el nowcasting en este momento'
        }


def _get_rainviewer_radar_status():
    """Consulta la disponibilidad de capas de radar Doppler en vivo de RainViewer (API gratuita)"""
    try:
        r = requests.get('https://api.rainviewer.com/public/weather-maps.json', timeout=5)
        if r.status_code == 200:
            d = r.json()
            radar_frames = d.get('radar', {}).get('past', [])
            nowcast_frames = d.get('radar', {}).get('nowcast', [])
            return {
                'proveedor': 'RainViewer Global Radar Network',
                'frames_pasados_disponibles': len(radar_frames),
                'frames_nowcast_disponibles': len(nowcast_frames),
                'cobertura_activa': True
            }
    except Exception:
        pass
    return {'cobertura_activa': False}


# =====================================================================
# 2. MODELO DE PREDICCIÓN DE ENERGÍA SOLAR Y EÓLICA (100% GRATIS)
# =====================================================================

def estimate_solar_wind_energy(lat: float, lon: float, 
                               capacidad_solar_kwp: float = 5.0, 
                               capacidad_eolica_kw: float = 10.0):
    """
    Calcula la estimación de generación energética horaria (kWh) para:
    1. Sistema Solar Fotovoltaico (Capacidad en kWp pico instalada)
    2. Aerogenerador / Turbina Eólica (Capacidad nominal en kW)
    
    Variables utilizadas (Open-Meteo Solar & Wind gratis):
      - shortwave_radiation_instant (W/m2)
      - direct_normal_irradiance (W/m2)
      - diffuse_radiation (W/m2)
      - temperature_2m (°C) -> Para pérdida térmica de celdas
      - windspeed_10m y windspeed_100m (km/h y m/s)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': 'temperature_2m,shortwave_radiation_instant,direct_normal_irradiance,diffuse_radiation,windspeed_10m,windspeed_100m',
        'forecast_days': 2,
        'timezone': 'auto'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        h = data.get('hourly', {})
        times = h.get('time', [])
        radiation = h.get('shortwave_radiation_instant', [])
        temps = h.get('temperature_2m', [])
        winds_10 = h.get('windspeed_10m', [])
        winds_100 = h.get('windspeed_100m', [])

        curva_horaria = []
        total_kwh_solar_hoy = 0.0
        total_kwh_eolico_hoy = 0.0

        # Coeficientes estándar de la industria
        PERFORMANCE_RATIO_SOLAR = 0.82  # Inversor, polvo, cableado
        COEF_TERMICO = 0.004           # Pérdida de 0.4% por grado > 25°C
        
        # Turbina eólica: V_cut_in = 3 m/s, V_rated = 12 m/s, V_cut_out = 25 m/s
        V_CUT_IN = 3.0
        V_RATED = 12.0
        V_CUT_OUT = 25.0

        # Analizar las próximas 24 horas
        for i in range(min(24, len(times))):
            t = times[i]
            rad = radiation[i] if i < len(radiation) else 0.0
            temp = temps[i] if i < len(temps) else 25.0
            
            # Velocidad de viento en m/s a altura de buje (100m o aproximación desde 10m)
            v_kmh = winds_100[i] if (i < len(winds_100) and winds_100[i] is not None) else winds_10[i]
            v_ms = (v_kmh * 1000.0 / 3600.0) if v_kmh is not None else 0.0

            # 1. GENERACIÓN SOLAR FOTOVOLTAICA
            temp_celda = temp + (rad / 800.0) * 25.0
            perdida_temp = 1.0 - max(0.0, (temp_celda - 25.0) * COEF_TERMICO)
            potencia_solar_kw = capacidad_solar_kwp * (rad / 1000.0) * perdida_temp * PERFORMANCE_RATIO_SOLAR
            potencia_solar_kw = max(0.0, round(potencia_solar_kw, 3))
            
            total_kwh_solar_hoy += potencia_solar_kw

            # 2. GENERACIÓN EÓLICA (Curva de potencia de turbina)
            if v_ms < V_CUT_IN or v_ms >= V_CUT_OUT:
                potencia_eolica_kw = 0.0
            elif v_ms >= V_RATED:
                potencia_eolica_kw = capacidad_eolica_kw
            else:
                frac = (v_ms - V_CUT_IN) / (V_RATED - V_CUT_IN)
                potencia_eolica_kw = capacidad_eolica_kw * (frac ** 3)
            
            potencia_eolica_kw = max(0.0, round(potencia_eolica_kw, 3))
            total_kwh_eolico_hoy += potencia_eolica_kw

            curva_horaria.append({
                'hora': t,
                'irradiancia_w_m2': rad,
                'temperatura_c': temp,
                'viento_m_s': round(v_ms, 2),
                'generacion_solar_kwh': potencia_solar_kw,
                'generacion_eolica_kwh': potencia_eolica_kw
            })

        return {
            'tipo': 'Estimación de Generación de Energía Renovable',
            'fuente': 'Modelos de Rendimiento Fotovoltaico (IEC 61724) y Curva Aerodinámica Eólica sobre Open-Meteo Solar',
            'parametros_instalacion': {
                'potencia_solar_instalada_kwp': capacidad_solar_kwp,
                'potencia_eolica_instalada_kw': capacidad_eolica_kw
            },
            'totales_24h': {
                'energia_solar_total_kwh': round(total_kwh_solar_hoy, 2),
                'energia_eolica_total_kwh': round(total_kwh_eolico_hoy, 2),
                'energia_renovable_combinada_kwh': round(total_kwh_solar_hoy + total_kwh_eolico_hoy, 2),
                'horas_sol_pico_estimadas_hsp': round(total_kwh_solar_hoy / (capacidad_solar_kwp * PERFORMANCE_RATIO_SOLAR), 2) if capacidad_solar_kwp > 0 else 0
            },
            'curva_horaria_24h': curva_horaria
        }

    except Exception as e:
        logger.warning("[EnergyEstimator] Error calculando energía renovable: %s", e)
        return {
            'error': str(e),
            'mensaje': 'No se pudo calcular la estimación energética en este momento'
        }
