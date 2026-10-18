# Rutas/Endpoints de la API

from app.routes.auth import auth_bp
from app.routes.usuarios import usuarios_bp
from app.routes.api_keys import api_keys_bp
from app.routes.consultas import consultas_bp
from app.routes.datos import datos_bp
from app.routes.dashboard import dashboard_bp

# Para que el __init__.py principal los encuentre
__all__ = ['auth_bp', 'usuarios_bp', 'api_keys_bp', 'consultas_bp', 'datos_bp', 'dashboard_bp']