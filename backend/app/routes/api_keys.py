# Gestión de API keys
"""
Rutas de API Keys
=================
Endpoints para gestión de API keys de proveedores
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.api_key import APIKey
from app.models.logs_actividad import LogsActividad
from cryptography.fernet import Fernet
import os
import base64

api_keys_bp = Blueprint('api_keys', __name__)


def get_cipher():
    """Obtener cipher para encriptación/desencriptación"""
    key = os.environ.get('ENCRYPTION_KEY', '')
    # Asegurar que la key tenga el formato correcto para Fernet (32 bytes, base64url)
    key_bytes = key.encode('utf-8')
    key_b64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
    return Fernet(key_b64)


@api_keys_bp.route('/', methods=['GET'])
@jwt_required()
def get_api_keys():
    """
    Listar todas las API keys del usuario
    """
    usuario_id = get_jwt_identity()

    # El modelo usa 'servicio_nombre' como campo, no 'proveedor'
    api_keys = APIKey.query.filter_by(usuario_id=usuario_id).all()

    return jsonify({
        'api_keys': [key.to_dict() for key in api_keys]
    }), 200


@api_keys_bp.route('/', methods=['POST'])
@jwt_required()
def create_api_key():
    """
    Crear nueva API key

    Body JSON:
        - proveedor: string (requerido) - ej: openweather, meteoblue
        - api_key: string (requerido)
        - descripcion: string (opcional)
    """
    usuario_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('proveedor') or not data.get('api_key'):
        return jsonify({'error': 'Proveedor y API key son requeridos'}), 400

    # Verificar si ya existe una key para este proveedor
    existing = APIKey.query.filter_by(
        usuario_id=usuario_id,
        servicio_nombre=data['proveedor']
    ).first()

    if existing:
        return jsonify({
            'error': f'Ya existe una API key para {data["proveedor"]}. Use PUT para actualizar.'
        }), 409

    # Crear usando el constructor del modelo (encripta automáticamente)
    api_key = APIKey(
        usuario_id=usuario_id,
        servicio_nombre=data['proveedor'],
        api_key_texto=data['api_key']
    )

    db.session.add(api_key)
    db.session.commit()

    # Registrar log
    log = LogsActividad(
        usuario_id=usuario_id,
        accion='create_api_key',
        detalle={'proveedor': data['proveedor']},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'message': 'API key guardada exitosamente',
        'api_key': api_key.to_dict()
    }), 201


@api_keys_bp.route('/<int:key_id>', methods=['GET'])
@jwt_required()
def get_api_key(key_id):
    """
    Obtener detalle de una API key
    """
    usuario_id = get_jwt_identity()

    api_key = APIKey.query.filter_by(id=key_id, usuario_id=usuario_id).first()
    if not api_key:
        return jsonify({'error': 'API key no encontrada'}), 404

    return jsonify({'api_key': api_key.to_dict()}), 200


@api_keys_bp.route('/<int:key_id>', methods=['PUT'])
@jwt_required()
def update_api_key(key_id):
    """
    Actualizar una API key
    """
    usuario_id = get_jwt_identity()

    api_key = APIKey.query.filter_by(id=key_id, usuario_id=usuario_id).first()
    if not api_key:
        return jsonify({'error': 'API key no encontrada'}), 404

    data = request.get_json()

    # Actualizar API key si se proporciona
    if data.get('api_key'):
        try:
            api_key.set_api_key(data['api_key'])
        except Exception as e:
            return jsonify({'error': 'Error al encriptar la API key'}), 500

    # Actualizar otros campos
    if 'descripcion' in data:
        # El modelo no tiene campo descripcion, se ignora si no existe
        pass
    if 'activa' in data:
        api_key.activa = data['activa']

    db.session.commit()

    # Registrar log
    log = LogsActividad(
        usuario_id=usuario_id,
        accion='update_api_key',
        detalle={'key_id': key_id, 'servicio': api_key.servicio_nombre},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'message': 'API key actualizada exitosamente',
        'api_key': api_key.to_dict()
    }), 200


@api_keys_bp.route('/<int:key_id>', methods=['DELETE'])
@jwt_required()
def delete_api_key(key_id):
    """
    Eliminar una API key
    """
    usuario_id = get_jwt_identity()

    api_key = APIKey.query.filter_by(id=key_id, usuario_id=usuario_id).first()
    if not api_key:
        return jsonify({'error': 'API key no encontrada'}), 404

    servicio = api_key.servicio_nombre

    db.session.delete(api_key)
    db.session.commit()

    # Registrar log
    log = LogsActividad(
        usuario_id=usuario_id,
        accion='delete_api_key',
        detalle={'key_id': key_id, 'servicio': servicio},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': 'API key eliminada exitosamente'}), 200


@api_keys_bp.route('/proveedores', methods=['GET'])
@jwt_required()
def get_proveedores():
    """
    Listar proveedores disponibles
    """
    proveedores = [
        {'id': 'openweather', 'nombre': 'OpenWeatherMap', 'requiere_secret': False},
        {'id': 'openmeteo', 'nombre': 'Open-Meteo', 'requiere_secret': False, 'gratuito': True},
        {'id': 'meteoblue', 'nombre': 'Meteoblue', 'requiere_secret': True},
        {'id': 'meteosource', 'nombre': 'Meteosource', 'requiere_secret': False},
        {'id': 'ideam', 'nombre': 'IDEAM Colombia', 'requiere_secret': False, 'gratuito': True},
        {'id': 'siata', 'nombre': 'SIATA Medellín', 'requiere_secret': False, 'gratuito': True}
    ]

    return jsonify({'proveedores': proveedores}), 200
