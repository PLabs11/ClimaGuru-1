"""
Motor de Inteligencia Meteorológica y Asistente de Toma de Decisiones
=====================================================================
Convierte los datos meteorológicos crudos en dictámenes y recomendaciones
estratégicas para 4 sectores críticos:
  1. Agricultura de Precisión
  2. Aviación y Operaciones Aéreas (VFR/IFR)
  3. Logística y Transporte Terrestre
  4. Prevención de Desastres y Gestión del Riesgo (Defensa Civil)

Arquitectura:
- Capa 1: Reglas físicas y heurísticas deterministas (100% confiables, sin alucinaciones).
- Capa 2: Síntesis de lenguaje natural lista para LangGraph / Agente LLM.
"""

import math
from typing import Dict, Any, Optional


def evaluate_decision_intelligence(weather_data: Dict[str, Any], 
                                  sector: Optional[str] = "todos") -> Dict[str, Any]:
    """
    Evalúa las condiciones meteorológicas y emite recomendaciones de decisión
    para uno o todos los sectores.
    
    Args:
        weather_data: Diccionario con temperatura, humedad, viento, lluvia, etc.
        sector: 'agricultura', 'aviacion', 'logistica', 'gestion_riesgo' o 'todos'
    """
    temp = weather_data.get('temperatura', 22.0) or 22.0
    hum = weather_data.get('humedad', 65) or 65
    viento_kmh = weather_data.get('velocidad_viento', 10.0) or 10.0
    precip_mm = weather_data.get('precipitacion', 0.0) or 0.0
    presion = weather_data.get('presion', 1013.25) or 1013.25
    ciudad = weather_data.get('ciudad', 'Ubicación')

    # Cálculos físicos base
    # Punto de rocío (Magnus formula)
    a, b = 17.27, 237.7
    alpha = ((a * temp) / (b + temp)) + math.log(max(hum, 1) / 100.0)
    punto_rocio = round((b * alpha) / (a - alpha), 1)

    # Techo de nubes estimado (Cloud Base AGL en metros y pies)
    # H (metros) ≈ 125 * (T - Td)
    techo_nubes_m = max(100, round(125 * max(0.1, temp - punto_rocio)))
    techo_nubes_ft = round(techo_nubes_m * 3.28084)

    # Densidad del aire estimada (kg/m3)
    p_pa = presion * 100.0
    densidad_aire = round(p_pa / (287.058 * (temp + 273.15)), 3)

    resultado = {
        'ciudad': ciudad,
        'metricas_meteorologicas': {
            'temperatura_c': temp,
            'humedad_porcentaje': hum,
            'viento_kmh': viento_kmh,
            'precipitacion_mm': precip_mm,
            'punto_rocio_c': punto_rocio,
            'techo_nubes_estimado_m': techo_nubes_m,
            'techo_nubes_estimado_ft': techo_nubes_ft,
            'densidad_aire_kg_m3': densidad_aire
        },
        'analisis_sectorial': {}
    }

    # 1. AGRICULTURA
    if sector in ['todos', 'agricultura']:
        riesgo_helada = temp <= 3.5 and hum < 75
        ventana_fumigacion = (3.0 <= viento_kmh <= 14.0) and (precip_mm == 0) and (temp < 28.0)
        
        score_agricola = 100
        if riesgo_helada: score_agricola -= 50
        if not ventana_fumigacion: score_agricola -= 20
        if precip_mm > 15: score_agricola -= 30

        resultado['analisis_sectorial']['agricultura'] = {
            'indice_viabilidad_labores': f"{max(0, score_agricola)}%",
            'alerta_helada': 'Riesgo Crítico de Helada' if riesgo_helada else 'Sin riesgo de helada',
            'ventana_fumigacion_optima': ventana_fumigacion,
            'recomendaciones': [
                "Condición ideal para aspersión y fumigación" if ventana_fumigacion else "No pulverizar: riesgo de deriva por viento o lavado por humedad/lluvia.",
                "Activar sistemas de riego anti-helada durante la madrugada" if riesgo_helada else "Régimen hídrico estándar para el cultivo.",
                "Ventilar invernaderos por riesgo de proliferación de hongos" if hum > 85 else "Humedad relativa en rango normal para follaje."
            ]
        }

    # 2. AVIACIÓN (VFR / IFR)
    if sector in ['todos', 'aviacion']:
        categoria_vuelo = "VFR (Vuelo Visual Permitido)"
        if techo_nubes_ft < 1000 or precip_mm > 10:
            categoria_vuelo = "IFR (Vuelo Instrumental Estricto)"
        elif techo_nubes_ft < 3000 or precip_mm > 2:
            categoria_vuelo = "MVFR (VFR Marginal - Precaución)"

        turbulencia_baja = "Moderada a Fuerte" if viento_kmh > 35 else ("Leve" if viento_kmh > 18 else "Nula / Aire Calmo")

        resultado['analisis_sectorial']['aviacion'] = {
            'categoria_operacional': categoria_vuelo,
            'techo_nuboso_agl': f"{techo_nubes_ft} ft ({techo_nubes_m} m)",
            'turbulencia_baja_altura': turbulencia_baja,
            'viento_superficie_nudos': round(viento_kmh / 1.852, 1),
            'recomendaciones': [
                f"Condición de vuelo declarada: {categoria_vuelo}.",
                "Monitorear aproximaciones por cizalladura o ráfagas térmicas" if viento_kmh > 25 else "Vientos calmos en cabecera de pista.",
                "Posible restricción visual en descensos por bajo techo de nubes" if techo_nubes_ft < 1500 else "Techo de nubes despejado para maniobras VFR."
            ]
        }

    # 3. LOGÍSTICA Y TRANSPORTE TERRESTRE
    if sector in ['todos', 'logistica']:
        riesgo_hidroplaneo = precip_mm >= 3.0
        riesgo_deslizamiento = precip_mm >= 20.0
        viento_cruzado_camiones = viento_kmh >= 40.0

        retraso_estimado = "Sin retrasos meteorológicos previstos"
        if precip_mm > 15 or viento_kmh > 45:
            retraso_estimado = "Retrasos severos estimados (+40% tiempo de ruta)"
        elif precip_mm > 5:
            retraso_estimado = "Retrasos moderados estimados (+15% a +25% tiempo de ruta)"

        resultado['analisis_sectorial']['logistica'] = {
            'estado_corredor_vial': "Transitable con Precaución" if (riesgo_hidroplaneo or riesgo_deslizamiento) else "Transitable Normal",
            'impacto_en_tiempos_entrega': retraso_estimado,
            'riesgo_hidroplaneo_en_calzada': riesgo_hidroplaneo,
            'alerta_viento_cruzado_camiones': viento_cruzado_camiones,
            'recomendaciones': [
                "Reducir velocidad en curvas y aumentar distancia de frenado" if riesgo_hidroplaneo else "Superficie de rodamiento seca.",
                "Alerta en zonas de cordillera y taludes por acumulación de agua" if riesgo_deslizamiento else "Estabilidad geológica en vía normal.",
                "Sujeción de carga y precaución con remolques de lona" if viento_cruzado_camiones else "Viento seguro para transporte de carga pesada."
            ]
        }

    # 4. GESTIÓN DEL RIESGO Y DEFENSA CIVIL
    if sector in ['todos', 'gestion_riesgo']:
        nivel_alerta = "VERDE (Condiciones Normales)"
        color_hex = "#22c55e"
        
        if precip_mm >= 30 or viento_kmh >= 60:
            nivel_alerta = "ROJO (Alerta Máxima - Emergencia Probable)"
            color_hex = "#ef4444"
        elif precip_mm >= 15 or viento_kmh >= 45:
            nivel_alerta = "NARANJA (Riesgo Alto - Preparar Evacuaciones Preventivas)"
            color_hex = "#f97316"
        elif precip_mm >= 5 or viento_kmh >= 30:
            nivel_alerta = "AMARILLO (Vigilancia Activa)"
            color_hex = "#eab308"

        resultado['analisis_sectorial']['gestion_riesgo'] = {
            'semaforo_alerta': nivel_alerta,
            'codigo_color': color_hex,
            'riesgo_crecientes_subitas': precip_mm >= 12.0,
            'riesgo_vendaval_caida_arboles': viento_kmh >= 40.0,
            'recomendaciones': [
                f"Protocolo activado: {nivel_alerta}.",
                "Monitorear niveles de quebradas y cauces hídricos urbanos" if precip_mm >= 10 else "Caudales en niveles de estiaje o promedio.",
                "Inspección de cubiertas, techos y tendido eléctrico" if viento_kmh >= 35 else "Sin amenaza de vendaval."
            ]
        }

    # Resumen ejecutivo para el Asistente Inteligente
    resultado['dictamen_ejecutivo_ia'] = (
        f"Informe de Inteligencia Meteorológica para {ciudad}: "
        f"Temperatura de {temp}°C con {hum}% de humedad relativa y vientos de {viento_kmh} km/h. "
        f"Precipitación instantánea estimada en {precip_mm} mm. "
        f"Se recomienda prestar atención particular al sector "
        f"{'Aviación y Logística' if precip_mm > 5 or viento_kmh > 30 else 'Agrícola (favorable)'}."
    )

    return resultado
