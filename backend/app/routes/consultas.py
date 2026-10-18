# Realizar consultas meteorológicas
"""
Rutas de Consultas
==================
Endpoints para realizar consultas meteorológicas
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import db
from app.models.consulta import Consulta
from app.models.dato_meteorologico import DatosClima
from app.models.logs_actividad import LogsActividad

consultas_bp = Blueprint('consultas', __name__)


import time
from app.services.weather_service import get_weather_aggregated, geocode_city

@consultas_bp.route('/tiempo-real', methods=['POST'])
@consultas_bp.route('', methods=['POST'])
@consultas_bp.route('/', methods=['POST'])
@jwt_required()
def consulta_tiempo_real():
    """
    Realizar consulta de clima (actual, pronóstico o histórico)
    y almacenar los resultados en la base de datos MySQL.
    """
    usuario_id = get_jwt_identity()
    data = request.get_json() or {}
    t0 = time.time()
    
    ciudad = data.get('ciudad')
    lat = data.get('latitud')
    lon = data.get('longitud')
    tipo_solicitado = data.get('tipo_consulta', 'actual').lower()
    
    # Normalizar tipo
    if tipo_solicitado in ['tiempo_real', 'actual', 'tiempo-real']:
        tipo_query = 'actual'
        db_tipo = 'actual'
    elif tipo_solicitado == 'pronostico':
        tipo_query = 'pronostico'
        db_tipo = 'pronostico'
    elif tipo_solicitado == 'historico':
        tipo_query = 'historico'
        db_tipo = 'historico'
    else:
        tipo_query = 'actual'
        db_tipo = 'actual'

    # Geocodificar si no hay lat/lon
    if (lat is None or lon is None) and ciudad:
        lat, lon = geocode_city(ciudad)
    
    if lat is None or lon is None:
        return jsonify({
            'error': 'No se pudo determinar la ubicación. Proporciona una ciudad válida o coordenadas (latitud, longitud).'
        }), 400

    lat = float(lat)
    lon = float(lon)
    if not ciudad:
        ciudad = f"Coord ({round(lat, 3)}, {round(lon, 3)})"
    
    # Crear registro de consulta en MySQL
    consulta = Consulta(
        usuario_id=usuario_id,
        tipo_consulta=db_tipo,
        ciudad=ciudad,
        latitud=lat,
        longitud=lon,
        fecha_inicio=data.get('fecha_inicio'),
        fecha_fin=data.get('fecha_fin'),
        formato_salida=data.get('formato', 'json'),
        parametros_solicitados=data.get('parametros', ['temperatura', 'humedad', 'viento', 'presion']),
        estado='procesando',
        ip_origen=request.remote_addr
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    try:
        # Obtener clima real agregado de todas las fuentes:
        # Meteoblue, Meteosource, OpenWeatherMap, IDEAM y Open-Meteo
        weather = get_weather_aggregated(lat, lon, tipo=tipo_query)
        
        # Guardar datos meteorológicos en MySQL (tabla datos_clima)
        datos_clima = DatosClima(
            consulta_id=consulta.id,
            temperatura_promedio=weather.get('temperatura'),
            temperatura_min=weather.get('temperatura_min'),
            temperatura_max=weather.get('temperatura_max'),
            humedad_relativa=int(weather['humedad']) if weather.get('humedad') is not None else None,
            presion_atmosferica=weather.get('presion'),
            velocidad_viento=weather.get('velocidad_viento'),
            direccion_viento=int(weather['direccion_viento']) if weather.get('direccion_viento') is not None else None,
            precipitacion=weather.get('precipitacion', 0),
            descripcion_clima=weather.get('descripcion', ''),
            fuentes_utilizadas=weather.get('fuentes', []),
            datos_completos=weather
        )
        
        db.session.add(datos_clima)
        
        # Actualizar estado de consulta en MySQL
        tiempo_ms = int((time.time() - t0) * 1000)
        consulta.estado = 'completada'
        consulta.completada_en = datetime.utcnow()
        consulta.tiempo_respuesta_ms = tiempo_ms
        db.session.commit()
        
        # Registrar log de actividad
        try:
            log = LogsActividad(
                usuario_id=usuario_id,
                accion=f'consulta_{db_tipo}',
                detalle={
                    'consulta_id': consulta.id,
                    'ciudad': consulta.ciudad,
                    'coordenadas': f"{consulta.latitud}, {consulta.longitud}",
                    'fuentes': weather.get('fuentes', [])
                },
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            pass

        fuentes_lista = weather.get('fuentes', [])
        return jsonify({
            'consulta': consulta.to_dict(),
            'datos': datos_clima.to_dict(),
            'datos_clima': {
                'temperatura': float(datos_clima.temperatura_promedio) if datos_clima.temperatura_promedio is not None else None,
                'temperatura_min': float(datos_clima.temperatura_min) if datos_clima.temperatura_min is not None else None,
                'temperatura_max': float(datos_clima.temperatura_max) if datos_clima.temperatura_max is not None else None,
                'humedad': datos_clima.humedad_relativa,
                'presion': float(datos_clima.presion_atmosferica) if datos_clima.presion_atmosferica is not None else None,
                'viento_vel': float(datos_clima.velocidad_viento) if datos_clima.velocidad_viento is not None else None,
                'viento_dir': f"{datos_clima.direccion_viento}°" if datos_clima.direccion_viento is not None else "",
                'precipitacion': float(datos_clima.precipitacion) if datos_clima.precipitacion is not None else 0,
                'descripcion': datos_clima.descripcion_clima or '',
                'fuentes': ', '.join(fuentes_lista),
                'fuentes_lista': fuentes_lista,
                'pronostico': weather.get('pronostico', []),
                'historico_diario': weather.get('historico_diario', []),
                'estaciones_ideam': weather.get('estaciones_ideam', [])
            }
        }), 200
        
    except Exception as e:
        consulta.estado = 'error'
        consulta.mensaje_error = str(e)
        db.session.commit()
        return jsonify({
            'error': 'Error al procesar la consulta meteorológica',
            'message': str(e)
        }), 500


@consultas_bp.route('/historico', methods=['POST'])
@jwt_required()
def consulta_historico():
    """
    Realizar consulta histórica (IDEAM y Reanálisis ERA5)
    y almacenar en MySQL
    """
    usuario_id = get_jwt_identity()
    data = request.get_json() or {}
    t0 = time.time()
    
    ciudad = data.get('ciudad')
    lat = data.get('latitud')
    lon = data.get('longitud')
    
    if (lat is None or lon is None) and ciudad:
        lat, lon = geocode_city(ciudad)
        
    if lat is None or lon is None:
        return jsonify({'error': 'Debe proporcionar ciudad o coordenadas válidas'}), 400

    lat = float(lat)
    lon = float(lon)
    if not ciudad:
        ciudad = f"Coord ({round(lat, 3)}, {round(lon, 3)})"
    
    consulta = Consulta(
        usuario_id=usuario_id,
        tipo_consulta='historico',
        ciudad=ciudad,
        latitud=lat,
        longitud=lon,
        fecha_inicio=data.get('fecha_inicio'),
        fecha_fin=data.get('fecha_fin'),
        formato_salida=data.get('formato', 'json'),
        parametros_solicitados=data.get('parametros', ['temperatura', 'precipitacion', 'humedad']),
        estado='procesando',
        ip_origen=request.remote_addr
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    try:
        weather = get_weather_aggregated(lat, lon, tipo='historico')
        
        datos_clima = DatosClima(
            consulta_id=consulta.id,
            temperatura_promedio=weather.get('temperatura'),
            temperatura_min=weather.get('temperatura_min'),
            temperatura_max=weather.get('temperatura_max'),
            humedad_relativa=int(weather['humedad']) if weather.get('humedad') is not None else None,
            presion_atmosferica=weather.get('presion', 1013.2),
            velocidad_viento=weather.get('velocidad_viento'),
            direccion_viento=weather.get('direccion_viento'),
            precipitacion=weather.get('precipitacion', 0),
            descripcion_clima=weather.get('descripcion', 'Historial IDEAM'),
            fuentes_utilizadas=weather.get('fuentes', ['IDEAM / ERA5']),
            datos_completos=weather
        )
        db.session.add(datos_clima)
        
        consulta.estado = 'completada'
        consulta.completada_en = datetime.utcnow()
        consulta.tiempo_respuesta_ms = int((time.time() - t0) * 1000)
        db.session.commit()
        
        return jsonify({
            'message': 'Consulta histórica procesada y guardada en BD',
            'consulta': consulta.to_dict(),
            'datos': datos_clima.to_dict(),
            'datos_clima': {
                'temperatura': float(datos_clima.temperatura_promedio) if datos_clima.temperatura_promedio is not None else None,
                'humedad': datos_clima.humedad_relativa,
                'presion': float(datos_clima.presion_atmosferica) if datos_clima.presion_atmosferica is not None else None,
                'precipitacion': float(datos_clima.precipitacion) if datos_clima.precipitacion is not None else 0,
                'fuentes': ', '.join(weather.get('fuentes', ['IDEAM'])),
                'fuentes_lista': weather.get('fuentes', ['IDEAM']),
                'historico_diario': weather.get('historico_diario', []),
                'estaciones_ideam': weather.get('estaciones_ideam', [])
            }
        }), 200
        
    except Exception as e:
        consulta.estado = 'error'
        consulta.mensaje_error = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@consultas_bp.route('/mis-consultas', methods=['GET'])
@consultas_bp.route('', methods=['GET'])
@consultas_bp.route('/', methods=['GET'])
@jwt_required()
def get_mis_consultas():
    """
    Obtener historial de consultas del usuario
    
    Query params:
        - page: int (default: 1)
        - per_page: int (default: 10, max: 100)
        - tipo: string (tiempo_real, historico)
        - estado: string (pendiente, procesando, completada, error)
    
    Returns:
        - consultas: lista de consultas
        - total: total de consultas
        - pages: total de páginas
    """
    usuario_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    
    query = Consulta.query.filter_by(usuario_id=usuario_id)
    
    if tipo:
        query = query.filter_by(tipo_consulta=tipo)
    if estado:
        query = query.filter_by(estado=estado)
    
    pagination = query.order_by(Consulta.creada_en.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'consultas': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@consultas_bp.route('/<int:consulta_id>', methods=['GET'])
@jwt_required()
def get_consulta(consulta_id):
    """
    Obtener detalle de una consulta específica
    
    Args:
        consulta_id: ID de la consulta
    
    Returns:
        - consulta: datos de la consulta
        - datos_clima: datos climáticos asociados (si existen)
    """
    usuario_id = get_jwt_identity()
    
    consulta = Consulta.query.filter_by(id=consulta_id, usuario_id=usuario_id).first()
    
    if not consulta:
        return jsonify({'error': 'Consulta no encontrada'}), 404
    
    response = {'consulta': consulta.to_dict()}
    
    if consulta.datos_clima:
        response['datos_clima'] = consulta.datos_clima.to_dict()
    
    return jsonify(response), 200


@consultas_bp.route('/<int:consulta_id>/descargar', methods=['GET'])
@jwt_required()
def descargar_consulta(consulta_id):
    """
    Descargar datos de una consulta en el formato solicitado
    
    Args:
        consulta_id: ID de la consulta
    
    Returns:
        - Archivo en formato JSON, CSV, TXT o YAML
    """
    usuario_id = get_jwt_identity()
    
    consulta = Consulta.query.filter_by(id=consulta_id, usuario_id=usuario_id).first()
    
    if not consulta:
        return jsonify({'error': 'Consulta no encontrada'}), 404
    
    if consulta.estado != 'completada':
        return jsonify({'error': 'La consulta no está completada'}), 400
    
    if not consulta.datos_clima:
        return jsonify({'error': 'No hay datos disponibles'}), 404
    
    formato = consulta.formato_salida
    datos = consulta.datos_clima.to_dict()
    
    if formato == 'json':
        return jsonify(datos), 200
    
    elif formato == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(['Parametro', 'Valor'])
        
        # Escribir datos
        writer.writerow(['Temperatura Promedio', datos['temperatura']['promedio']])
        writer.writerow(['Temperatura Min', datos['temperatura']['min']])
        writer.writerow(['Temperatura Max', datos['temperatura']['max']])
        writer.writerow(['Presion', datos['presion_atmosferica']])
        writer.writerow(['Humedad', datos['humedad_relativa']])
        writer.writerow(['Viento Velocidad', datos['viento']['velocidad']])
        writer.writerow(['Viento Direccion', datos['viento']['direccion']])
        
        output.seek(0)
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=consulta_{consulta_id}.csv'
        }
    
    elif formato == 'txt':
        texto = f"""
CONSULTA CLIMÁTICA - ClimaGuru
==============================
ID Consulta: {consulta_id}
Fecha: {consulta.creada_en}

DATOS OBTENIDOS:
----------------
Temperatura: {datos['temperatura']['promedio']}°C
  - Mínima: {datos['temperatura']['min']}°C
  - Máxima: {datos['temperatura']['max']}°C
Presión Atmosférica: {datos['presion_atmosferica']} hPa
Humedad: {datos['humedad_relativa']}%
Viento: {datos['viento']['velocidad']} km/h, dirección {datos['viento']['direccion']}°
Descripción: {datos['descripcion_clima']}

Fuentes: {', '.join(datos['fuentes_utilizadas'] or [])}
"""
        return texto, 200, {'Content-Type': 'text/plain'}
    
    elif formato == 'yaml':
        try:
            import yaml
            return yaml.dump(datos), 200, {'Content-Type': 'text/yaml'}
        except ImportError:
            return jsonify({'error': 'Formato YAML no disponible'}), 500
    
    return jsonify({'error': 'Formato no soportado'}), 400


# =====================================================================
# ENDPOINTS ESPECIALIZADOS: NMM METEOBLUE, NOWCASTING, ENERGÍA Y DECISIÓN
# =====================================================================

from app.services.weather_service import get_meteoblue_nmm_dataset
from app.services.energy_and_nowcasting_service import get_free_minutely_nowcasting, estimate_solar_wind_energy
from app.services.ai_decision_engine import evaluate_decision_intelligence


@consultas_bp.route('/meteoblue/nmm', methods=['GET', 'POST'])
def meteoblue_nmm_endpoint():
    """
    Endpoint para consultar modelos numéricos NMM / NEMS de Meteoblue
    Query params o JSON body:
      - latitud: float (opcional si se envía ciudad)
      - longitud: float (opcional si se envía ciudad)
      - ciudad: string (ej: Medellin)
      - dominio: string (default: 'NMM18' para Suramérica, o 'NEMSAUTO')
    """
    data = request.get_json(silent=True) or {}
    ciudad = request.args.get('ciudad') or data.get('ciudad')
    lat = request.args.get('latitud', type=float) or data.get('latitud')
    lon = request.args.get('longitud', type=float) or data.get('longitud')
    dominio = request.args.get('dominio') or data.get('dominio') or 'NMM18'

    if (lat is None or lon is None) and ciudad:
        lat, lon = geocode_city(ciudad)

    if lat is None or lon is None:
        lat, lon = 6.2442, -75.5812

    resultado = get_meteoblue_nmm_dataset(float(lat), float(lon), domain=dominio)
    return jsonify(resultado), 200


@consultas_bp.route('/nowcasting', methods=['GET', 'POST'])
def nowcasting_endpoint():
    """
    Endpoint gratuito de Nowcasting de precipitación minuto a minuto (próximas 2 horas)
    Alternativa 100% gratuita a Meteosource Premium.
    """
    data = request.get_json(silent=True) or {}
    ciudad = request.args.get('ciudad') or data.get('ciudad')
    lat = request.args.get('latitud', type=float) or data.get('latitud')
    lon = request.args.get('longitud', type=float) or data.get('longitud')

    if (lat is None or lon is None) and ciudad:
        lat, lon = geocode_city(ciudad)

    if lat is None or lon is None:
        lat, lon = 6.2442, -75.5812

    resultado = get_free_minutely_nowcasting(float(lat), float(lon))
    return jsonify(resultado), 200


@consultas_bp.route('/energia-renovable', methods=['GET', 'POST'])
def energia_renovable_endpoint():
    """
    Endpoint gratuito de estimación de generación solar y eólica (kWh).
    Alternativa 100% gratuita a los modelos de energía de Meteosource.
    """
    data = request.get_json(silent=True) or {}
    ciudad = request.args.get('ciudad') or data.get('ciudad')
    lat = request.args.get('latitud', type=float) or data.get('latitud')
    lon = request.args.get('longitud', type=float) or data.get('longitud')
    kwp_solar = float(request.args.get('solar_kwp') or data.get('solar_kwp', 5.0))
    kw_eolica = float(request.args.get('eolica_kw') or data.get('eolica_kw', 10.0))

    if (lat is None or lon is None) and ciudad:
        lat, lon = geocode_city(ciudad)

    if lat is None or lon is None:
        lat, lon = 6.2442, -75.5812

    resultado = estimate_solar_wind_energy(float(lat), float(lon), kwp_solar, kw_eolica)
    return jsonify(resultado), 200


@consultas_bp.route('/analisis-decision', methods=['GET', 'POST'])
def analisis_decision_endpoint():
    """
    Asistente Inteligente de Toma de Decisiones Meteorológicas para:
      - Agricultura
      - Aviación
      - Logística
      - Gestión de Riesgo
    """
    data = request.get_json(silent=True) or {}
    ciudad = request.args.get('ciudad') or data.get('ciudad')
    lat = request.args.get('latitud', type=float) or data.get('latitud')
    lon = request.args.get('longitud', type=float) or data.get('longitud')
    sector = request.args.get('sector') or data.get('sector', 'todos')

    if (lat is None or lon is None) and ciudad:
        lat, lon = geocode_city(ciudad)

    if lat is None or lon is None:
        lat, lon = 6.2442, -75.5812
        ciudad = "Medellín"

    weather = get_weather_aggregated(float(lat), float(lon), tipo='actual')
    if ciudad and not weather.get('ciudad'):
        weather['ciudad'] = ciudad

    resultado = evaluate_decision_intelligence(weather, sector=sector)
    return jsonify(resultado), 200

