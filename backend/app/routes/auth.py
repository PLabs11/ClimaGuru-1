# Login, logout, registro
"""
Rutas de autenticación para ClimaGuru
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models.usuario import Usuario
from app.models.sesion import Sesion
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__)


def validar_email(email):
    """Validar formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def validar_password(password):
    """
    Validar fortaleza de contraseña
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    
    return True, "Contraseña válida"


@auth_bp.route('/registro', methods=['POST'])
@auth_bp.route('/register', methods=['POST'])
def registro():
    """
    Registrar nuevo usuario
    
    Body (JSON):
        - username: Nombre de usuario
        - email: Email
        - password: Contraseña
        - nombre_completo: Nombre completo (opcional)
    
    Returns:
        JSON con datos del usuario creado y tokens
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({
                'error': 'Faltan campos requeridos',
                'requeridos': ['username', 'email', 'password']
            }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        nombre_completo = data.get('nombre_completo', '').strip()
        
        # Validaciones
        if len(username) < 3:
            return jsonify({'error': 'El username debe tener al menos 3 caracteres'}), 400
        
        if not validar_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        valida, mensaje = validar_password(password)
        if not valida:
            return jsonify({'error': mensaje}), 400
        
        # Verificar si ya existe
        if Usuario.query.filter_by(username=username).first():
            return jsonify({'error': 'El username ya está registrado'}), 409
        
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        
        # Crear usuario
        nuevo_usuario = Usuario(
            username=username,
            email=email,
            password=password,
            nombre_completo=nombre_completo if nombre_completo else None
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Generar tokens
        access_token = create_access_token(identity=str(nuevo_usuario.id))
        refresh_token = create_refresh_token(identity=str(nuevo_usuario.id))
        
        # Crear sesión
        crear_sesion(nuevo_usuario.id, access_token)
        
        usuario_dict = nuevo_usuario.to_dict()
        return jsonify({
            'mensaje': 'Usuario registrado exitosamente',
            'usuario': usuario_dict,
            'user': usuario_dict,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al registrar usuario: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión
    
    Body (JSON):
        - username_or_email: Username o email
        - password: Contraseña
    
    Returns:
        JSON con tokens de acceso
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Faltan credenciales'}), 400
        
        username_or_email = data.get('username_or_email') or data.get('username') or data.get('email')
        if not username_or_email or not data.get('password'):
            return jsonify({'error': 'Faltan credenciales'}), 400
        
        username_or_email = str(username_or_email).strip()
        password = data['password']
        
        # Buscar usuario por username o email
        usuario = Usuario.query.filter(
            (Usuario.username == username_or_email) | 
            (Usuario.email == username_or_email.lower())
        ).first()
        
        if not usuario:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        if not usuario.activo:
            return jsonify({'error': 'Usuario inactivo'}), 403
        
        if not usuario.check_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Actualizar último acceso
        usuario.actualizar_ultimo_acceso()
        
        # Generar tokens
        access_token = create_access_token(identity=str(usuario.id))
        refresh_token = create_refresh_token(identity=str(usuario.id))
        
        # Crear sesión
        crear_sesion(usuario.id, access_token)
        
        usuario_dict = usuario.to_dict(include_stats=True)
        return jsonify({
            'mensaje': 'Login exitoso',
            'usuario': usuario_dict,
            'user': usuario_dict,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al iniciar sesión: {str(e)}'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refrescar token de acceso
    
    Headers:
        Authorization: Bearer {refresh_token}
    
    Returns:
        JSON con nuevo access_token
    """
    try:
        usuario_id = get_jwt_identity()
        nuevo_access_token = create_access_token(identity=str(usuario_id))
        
        # Actualizar sesión
        crear_sesion(usuario_id, nuevo_access_token)
        
        return jsonify({
            'access_token': nuevo_access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al refrescar token: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Cerrar sesión
    
    Headers:
        Authorization: Bearer {access_token}
    """
    try:
        usuario_id = get_jwt_identity()
        jti = get_jwt()['jti']  # JWT ID
        
        # Marcar sesión como inactiva
        sesion = Sesion.query.filter_by(token=jti, usuario_id=usuario_id).first()
        if sesion:
            sesion.activa = False
            db.session.commit()
        
        return jsonify({
            'mensaje': 'Sesión cerrada exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al cerrar sesión: {str(e)}'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def perfil():
    """
    Obtener información del usuario actual
    
    Headers:
        Authorization: Bearer {access_token}
    
    Returns:
        JSON con datos del usuario
    """
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(int(usuario_id))
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        usuario_dict = usuario.to_dict(include_stats=True)
        return jsonify({
            'usuario': usuario_dict,
            'user': usuario_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener perfil: {str(e)}'}), 500


def crear_sesion(usuario_id, token):
    """Helper para crear o actualizar sesión"""
    try:
        # Obtener información de la petición
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Calcular fecha de expiración (basada en JWT_ACCESS_TOKEN_EXPIRES)
        from flask import current_app
        expira_en = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))
        fecha_expiracion = datetime.utcnow() + expira_en
        
        # Crear nueva sesión
        nueva_sesion = Sesion(
            usuario_id=usuario_id,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
            fecha_expiracion=fecha_expiracion
        )
        
        db.session.add(nueva_sesion)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear sesión: {e}")
        # No fallar si no se puede crear la sesión
        pass