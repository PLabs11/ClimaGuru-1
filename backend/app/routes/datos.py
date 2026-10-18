"""
Rutas de Datos Meteorológicos
=============================
Endpoints para obtener registros históricos y análisis de datos climáticos guardados en la base de datos MySQL.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.extensions import db
from app.models.dato_meteorologico import DatosClima
from app.models.consulta import Consulta

datos_bp = Blueprint('datos', __name__)

@datos_bp.route('/historicos', methods=['GET'])
def get_historicos():
    """
    Obtener datos históricos guardados en la base de datos MySQL
    con soporte para paginación y filtro por ciudad.
    """
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        user_id = None

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    ciudad = request.args.get('ciudad')

    query = (
        db.session.query(DatosClima, Consulta)
        .join(Consulta, DatosClima.consulta_id == Consulta.id)
    )

    if user_id:
        query = query.filter(Consulta.usuario_id == user_id)
    if ciudad:
        query = query.filter(Consulta.ciudad.ilike(f'%{ciudad}%'))

    pagination = query.order_by(DatosClima.guardado_en.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    registros = []
    for dc, c in pagination.items:
        d = dc.to_dict()
        d['ciudad'] = c.ciudad
        d['tipo_consulta'] = c.tipo_consulta
        d['latitud'] = float(c.latitud) if c.latitud else None
        d['longitud'] = float(c.longitud) if c.longitud else None
        d['creada_en'] = c.creada_en.isoformat() if c.creada_en else None
        registros.append(d)

    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page,
        'datos': registros
    }), 200
