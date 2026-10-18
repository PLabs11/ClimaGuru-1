# Gestión de usuarios
"""
Rutas de Usuarios
=================
Endpoints para gestión de usuarios (solo admin)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.usuario import Usuario
from app.models.logs_actividad import LogsActividad
from functools import wraps

usuarios_bp = Blueprint('usuarios', __name__)


def admin_required(fn):
    """Decorador para verificar que el usuario es admin"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        if not usuario or usuario.rol != 'admin':
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return fn(*args, **kwargs)
    return wrapper


@usuarios_bp.route('/', methods=['GET'])
@jwt_required()
@admin_required
def get_usuarios():
    """
    Listar todos los usuarios (solo admin)
    
    Query params:
        - page: int (default: 1)
        - per_page: int (default: 20)
        - activo: bool
    
    Returns:
        - usuarios: lista de usuarios
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    activo = request.args.get('activo')
    
    query = Usuario.query
    if activo is not None:
        query = query.filter_by(activo=activo.lower() == 'true')
    
    pagination = query.order_by(Usuario.fecha_registro.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'usuarios': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@usuarios_bp.route('/<int:usuario_id>', methods=['GET'])
@jwt_required()
def get_usuario(usuario_id):
    """
    Obtener datos de un usuario específico
    Los usuarios solo pueden ver sus propios datos, los admin pueden ver todos
    """
    current_user_id = get_jwt_identity()
    current_user = Usuario.query.get(current_user_id)
    
    # Verificar permisos
    if current_user.rol != 'admin' and current_user_id != usuario_id:
        return jsonify({'error': 'No tiene permisos para ver este usuario'}), 403
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({'usuario': usuario.to_dict()}), 200


@usuarios_bp.route('/<int:usuario_id>', methods=['PUT'])
@jwt_required()
def update_usuario(usuario_id):
    """
    Actualizar datos de un usuario
    """
    current_user_id = get_jwt_identity()
    current_user = Usuario.query.get(current_user_id)
    
    if current_user.rol != 'admin' and current_user_id != usuario_id:
        return jsonify({'error': 'No tiene permisos para editar este usuario'}), 403
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.get_json()
    
    # Campos permitidos para actualizar
    if 'nombre_completo' in data:
        usuario.nombre_completo = data['nombre_completo']
    if 'email' in data:
        # Verificar que el email no esté en uso
        existing = Usuario.query.filter_by(email=data['email']).first()
        if existing and existing.id != usuario_id:
            return jsonify({'error': 'El email ya está en uso'}), 409
        usuario.email = data['email']
    
    # Solo admin puede cambiar rol y estado
    if current_user.rol == 'admin':
        if 'rol' in data:
            usuario.rol = data['rol']
        if 'activo' in data:
            usuario.activo = data['activo']
    
    db.session.commit()
    
    # Registrar log
    log = LogsActividad(
        usuario_id=current_user_id,
        accion='update_usuario',
        detalle={'usuario_id': usuario_id, 'campos': list(data.keys())},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Usuario actualizado exitosamente',
        'usuario': usuario.to_dict()
    }), 200


@usuarios_bp.route('/<int:usuario_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_usuario(usuario_id):
    """
    Desactivar/eliminar un usuario (solo admin)
    """
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # No permitir eliminar al último admin
    if usuario.rol == 'admin':
        admin_count = Usuario.query.filter_by(rol='admin', activo=True).count()
        if admin_count <= 1:
            return jsonify({'error': 'No puede eliminar el último administrador'}), 400
    
    # Soft delete: desactivar en lugar de eliminar
    usuario.activo = False
    db.session.commit()
    
    # Registrar log
    log = LogsActividad(
        usuario_id=get_jwt_identity(),
        accion='delete_usuario',
        detalle={'usuario_id': usuario_id, 'username': usuario.username},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Usuario desactivado exitosamente'}), 200


@usuarios_bp.route('/<int:usuario_id>/cambiar-password', methods=['POST'])
@jwt_required()
def cambiar_password(usuario_id):
    """
    Cambiar contraseña de un usuario
    """
    current_user_id = get_jwt_identity()
    current_user = Usuario.query.get(current_user_id)
    
    if current_user.rol != 'admin' and current_user_id != usuario_id:
        return jsonify({'error': 'No tiene permisos para cambiar esta contraseña'}), 403
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.get_json()
    
    # Si no es admin, requerir contraseña actual
    if current_user.rol != 'admin':
        if not data.get('password_actual') or not usuario.check_password(data['password_actual']):
            return jsonify({'error': 'Contraseña actual incorrecta'}), 401
    
    if not data.get('password_nueva') or len(data['password_nueva']) < 6:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
    
    usuario.set_password(data['password_nueva'])
    db.session.commit()
    
    # Registrar log
    log = LogsActividad(
        usuario_id=current_user_id,
        accion='cambiar_password',
        detalle={'usuario_id': usuario_id},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200
