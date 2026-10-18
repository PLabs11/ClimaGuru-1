"""
Modelo de API Keys para ClimaGuru
Mapeado exactamente con la tabla `api_keys` de la base de datos
"""
from app import db
from datetime import datetime
from cryptography.fernet import Fernet
from sqlalchemy.orm import synonym
import os
import base64


class APIKey(db.Model):
    """Modelo para almacenar API Keys de servicios meteorológicos"""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    proveedor = db.Column(db.String(50), nullable=False, index=True)
    api_key_encrypted = db.Column(db.Text, nullable=False)
    api_secret_encrypted = db.Column(db.Text, nullable=True)
    descripcion = db.Column(db.String(255), nullable=True)
    activa = db.Column(db.Boolean, default=True, index=True)
    limite_consultas_diarias = db.Column(db.Integer, default=1000)
    consultas_realizadas = db.Column(db.Integer, default=0)
    ultimo_uso = db.Column(db.DateTime, nullable=True)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Compatibilidad con código que use servicio_nombre o fecha_registro
    servicio_nombre = synonym('proveedor')
    fecha_registro = synonym('creada_en')
    fecha_actualizacion = synonym('actualizada_en')
    
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'proveedor', name='unique_proveedor_usuario'),
    )
    
    def __init__(self, usuario_id, proveedor=None, api_key_texto=None, servicio_nombre=None, descripcion=None, api_secret=None):
        self.usuario_id = usuario_id
        self.proveedor = proveedor or servicio_nombre
        self.descripcion = descripcion
        if api_key_texto:
            self.set_api_key(api_key_texto)
        if api_secret:
            self.set_api_secret(api_secret)
            
    def set_api_key(self, api_key_texto):
        """Encriptar y guardar API key"""
        cipher = self._get_cipher()
        self.api_key_encrypted = cipher.encrypt(api_key_texto.encode('utf-8')).decode('utf-8')
        self.actualizada_en = datetime.utcnow()
    
    def get_api_key(self):
        """Desencriptar y obtener API key"""
        if not self.api_key_encrypted:
            return ""
        try:
            cipher = self._get_cipher()
            return cipher.decrypt(self.api_key_encrypted.encode('utf-8')).decode('utf-8')
        except Exception:
            return self.api_key_encrypted

    def set_api_secret(self, secret_texto):
        """Encriptar y guardar API secret"""
        cipher = self._get_cipher()
        self.api_secret_encrypted = cipher.encrypt(secret_texto.encode('utf-8')).decode('utf-8')

    def get_api_secret(self):
        """Desencriptar API secret"""
        if not self.api_secret_encrypted:
            return None
        try:
            cipher = self._get_cipher()
            return cipher.decrypt(self.api_secret_encrypted.encode('utf-8')).decode('utf-8')
        except Exception:
            return self.api_secret_encrypted
    
    @staticmethod
    def _get_cipher():
        key = os.getenv('ENCRYPTION_KEY', 'climaguru_dev_encryption_key_32chars_ok!')
        key_bytes = key.encode('utf-8')
        key_b64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
        return Fernet(key_b64)
    
    def to_dict(self, include_key=True):
        """Convertir a diccionario"""
        key = self.get_api_key() if self.api_key_encrypted else ""
        data = {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'proveedor': self.proveedor,
            'servicio_nombre': self.proveedor,
            'descripcion': self.descripcion,
            'activa': bool(self.activa),
            'limite_consultas_diarias': self.limite_consultas_diarias,
            'consultas_realizadas': self.consultas_realizadas,
            'ultimo_uso': self.ultimo_uso.isoformat() if self.ultimo_uso else None,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None,
            'actualizada_en': self.actualizada_en.isoformat() if self.actualizada_en else None,
            'api_key': key,
            'api_key_preview': f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
        }
        return data
    
    def __repr__(self):
        return f'<APIKey {self.proveedor} - Usuario {self.usuario_id}>'