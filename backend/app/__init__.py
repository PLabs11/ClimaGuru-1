# Inicialización de la aplicación Flask
"""
ClimaGuru Backend - Factory Pattern
====================================
Inicialización de la aplicación Flask - ClimaGuru
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate, jwt
import os

# Re-exportar para compatibilidad con modelos que usan "from app import db"
__all__ = ['db', 'migrate', 'jwt']

# Inicializar extensiones
# db = SQLAlchemy()  # Ahora se importa de extensions.py
# migrate = Migrate()
# jwt = JWTManager()

def create_app(config_name=None):
    """
    Factory para crear la aplicación Flask
    
    Args:
        config_name: Nombre de la configuración ('development', 'production', 'testing')
    
    Returns:
        app: Instancia de Flask configurada
    """
    # Crear instancia de Flask
    app = Flask(__name__)
    
    # Cargar configuración
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, 
     resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"]
)
    
    # Importar modelos para que SQLAlchemy los registre
    from app.models import Usuario, APIKey, Consulta, DatosClima, Sesion, LogsActividad, CiudadesFavoritas
    
    # Inicializar base de datos (MySQL y SQLite)
    with app.app_context():
        from app.database import init_database
        if init_database(app):
            print("[OK] Base de datos inicializada correctamente")
        else:
            print("[WARN] La base de datos no esta disponible")
    
    # Registrar blueprints (rutas)
    register_blueprints(app)
    
    # Configurar logging
    setup_logging(app)
    
    # Handlers de errores
    register_error_handlers(app)
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    return app


def register_blueprints(app):
    """Registrar todos los blueprints de la aplicación"""
    from app.routes import auth_bp, usuarios_bp, api_keys_bp, consultas_bp, datos_bp, dashboard_bp
    
    # Registrar con prefijo /api
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(api_keys_bp, url_prefix='/api/api-keys')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    app.register_blueprint(datos_bp, url_prefix='/api/datos')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    # Ruta de salud del servidor
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'ClimaGuru API está funcionando'}, 200


def setup_logging(app):
    """Configurar sistema de logging"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not app.debug and not app.testing:
        # Configurar archivo de log
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
    app.logger.setLevel(logging.INFO)
    app.logger.info('ClimaGuru Backend iniciado')


def register_error_handlers(app):
    """Registrar manejadores de errores personalizados"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': 'No encontrado',
            'message': 'El recurso solicitado no existe'
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {
            'error': 'Error interno del servidor',
            'message': 'Ocurrió un error inesperado'
        }, 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return {
            'error': 'Prohibido',
            'message': 'No tienes permiso para acceder a este recurso'
        }, 403