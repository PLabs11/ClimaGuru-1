"""
Modelo de Sesión para ClimaGuru
"""
from app import db
from datetime import datetime


class Sesion(db.Model):
    """Modelo para gestionar sesiones de usuario"""
    
    __tablename__ = 'sesiones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    token = db.Column(db.String(500), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    activa = db.Column(db.Boolean, default=True, index=True)
    
    def __init__(self, usuario_id, token, ip_address=None, user_agent=None, fecha_expiracion=None):
        self.usuario_id = usuario_id
        self.token = token
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.fecha_expiracion = fecha_expiracion or datetime.utcnow()
    
    def esta_activa(self):
        """Verificar si la sesión está activa y no expirada"""
        return self.activa and self.fecha_expiracion > datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_expiracion': self.fecha_expiracion.isoformat(),
            'activa': self.activa,
            'expirada': self.fecha_expiracion <= datetime.utcnow()
        }
    
    def __repr__(self):
        return f'<Sesion Usuario:{self.usuario_id} Activa:{self.activa}>'