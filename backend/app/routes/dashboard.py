"""
Rutas de Dashboard para ClimaGuru
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.consulta import Consulta
from app.models.api_key import APIKey
from app.models.dato_meteorologico import DatosClima

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Obtener estadísticas del dashboard
    """
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        user_id = None

    # Base query de consultas
    query_consultas = Consulta.query
    query_keys = APIKey.query.filter_by(activa=True)
    if user_id:
        query_consultas = query_consultas.filter(Consulta.usuario_id == user_id)
        query_keys = query_keys.filter(APIKey.usuario_id == user_id)

    total_consultas = query_consultas.count()
    api_keys_activas = query_keys.count()

    # Consultas hoy
    hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    consultas_hoy = query_consultas.filter(Consulta.creada_en >= hoy_inicio).count()

    # Ciudades frecuentes (top 5)
    ciudades_query = (
        db.session.query(Consulta.ciudad, func.count(Consulta.id).label('count'))
        .filter(Consulta.ciudad.isnot(None))
    )
    if user_id:
        ciudades_query = ciudades_query.filter(Consulta.usuario_id == user_id)
    ciudades_res = (
        ciudades_query
        .group_by(Consulta.ciudad)
        .order_by(func.count(Consulta.id).desc())
        .limit(5)
        .all()
    )
    ciudades_frecuentes = [{'ciudad': r[0], 'count': r[1]} for r in ciudades_res]

    # Consultas por día (últimos 7 días)
    dias_semana = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
    consultas_por_dia = []
    ahora = datetime.utcnow()
    for i in range(6, -1, -1):
        dia = ahora - timedelta(days=i)
        dia_inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        dia_fin = dia_inicio + timedelta(days=1)
        cnt_q = query_consultas.filter(Consulta.creada_en >= dia_inicio, Consulta.creada_en < dia_fin)
        nombre_dia = dias_semana[dia.weekday()]
        consultas_por_dia.append({
            'fecha': nombre_dia,
            'count': cnt_q.count()
        })

    # Promedios climáticos
    prom_query = db.session.query(
        func.avg(DatosClima.temperatura_promedio).label('temp_avg'),
        func.avg(DatosClima.humedad_relativa).label('hum_avg'),
        func.avg(DatosClima.presion_atmosferica).label('pres_avg'),
        func.avg(DatosClima.velocidad_viento).label('viento_avg')
    )
    if user_id:
        prom_query = prom_query.join(Consulta, DatosClima.consulta_id == Consulta.id).filter(Consulta.usuario_id == user_id)
    prom_res = prom_query.first()

    promedios = {
        'temperatura': round(float(prom_res[0]), 1) if prom_res and prom_res[0] is not None else 22.0,
        'humedad': round(float(prom_res[1]), 1) if prom_res and prom_res[1] is not None else 65.0,
        'presion': round(float(prom_res[2]), 1) if prom_res and prom_res[2] is not None else 1013.2,
        'viento': round(float(prom_res[3]), 1) if prom_res and prom_res[3] is not None else 12.0
    }

    return jsonify({
        'total_consultas': total_consultas,
        'consultas_hoy': consultas_hoy,
        'api_keys_activas': api_keys_activas,
        'ciudades_frecuentes': ciudades_frecuentes,
        'consultas_por_dia': consultas_por_dia,
        'promedios': promedios
    }), 200
