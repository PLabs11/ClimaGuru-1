"""
Modelo: Consulta
================
Registra cada consulta meteorológica realizada
"""
from app import db
from datetime import datetime


class Consulta(db.Model):
    """Modelo de consulta meteorológica"""
    
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    tipo_consulta = db.Column(db.Enum('tiempo_real', 'historico', 'pronostico', 'actual', name='tipo_consulta_enum'),
                              nullable=False, index=True)
    ciudad = db.Column(db.String(100), index=True)
    latitud = db.Column(db.Numeric(10, 8), index=True)
    longitud = db.Column(db.Numeric(11, 8), index=True)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    formato_salida = db.Column(db.Enum('json', 'csv', 'txt', 'yaml', name='formato_enum'),
                               default='json')
    parametros_solicitados = db.Column(db.JSON)
    respuesta_api = db.Column(db.JSON)
    estado = db.Column(db.Enum('pendiente', 'procesando', 'completada', 'error', 
                               name='estado_enum'), 
                       default='pendiente', index=True)
    mensaje_error = db.Column(db.Text)
    tiempo_respuesta_ms = db.Column(db.Integer)
    ip_origen = db.Column(db.String(45))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completada_en = db.Column(db.DateTime)
    
    # Relación con datos procesados
    datos_clima = db.relationship('DatosClima', backref='consulta', uselist=False,
                                  cascade='all, delete-orphan', lazy='joined')
    
    def to_dict(self):
        """Convertir a diccionario incluyendo datos_clima asociados"""
        res = {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'tipo_consulta': self.tipo_consulta,
            'ciudad': self.ciudad,
            'latitud': float(self.latitud) if self.latitud else None,
            'longitud': float(self.longitud) if self.longitud else None,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'formato': self.formato_salida,
            'formato_salida': self.formato_salida,
            'parametros_solicitados': self.parametros_solicitados,
            'estado': self.estado,
            'mensaje_error': self.mensaje_error,
            'tiempo_respuesta_ms': self.tiempo_respuesta_ms,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None,
            'completada_en': self.completada_en.isoformat() if self.completada_en else None
        }
        if self.datos_clima:
            fuentes_str = ""
            if isinstance(self.datos_clima.fuentes_utilizadas, list):
                fuentes_str = ", ".join(self.datos_clima.fuentes_utilizadas)
            elif self.datos_clima.fuentes_utilizadas:
                fuentes_str = str(self.datos_clima.fuentes_utilizadas)

            res['datos_clima'] = {
                'id': self.datos_clima.id,
                'consulta_id': self.datos_clima.consulta_id,
                'temperatura': float(self.datos_clima.temperatura_promedio) if self.datos_clima.temperatura_promedio is not None else None,
                'temperatura_min': float(self.datos_clima.temperatura_min) if self.datos_clima.temperatura_min is not None else None,
                'temperatura_max': float(self.datos_clima.temperatura_max) if self.datos_clima.temperatura_max is not None else None,
                'presion': float(self.datos_clima.presion_atmosferica) if self.datos_clima.presion_atmosferica is not None else None,
                'humedad': self.datos_clima.humedad_relativa,
                'viento_vel': float(self.datos_clima.velocidad_viento) if self.datos_clima.velocidad_viento is not None else None,
                'viento_dir': f"{self.datos_clima.direccion_viento}°" if self.datos_clima.direccion_viento is not None else "",
                'precipitacion': float(self.datos_clima.precipitacion) if self.datos_clima.precipitacion is not None else 0,
                'descripcion': self.datos_clima.descripcion_clima or '',
                'fuentes': fuentes_str,
                'fuentes_lista': self.datos_clima.fuentes_utilizadas if isinstance(self.datos_clima.fuentes_utilizadas, list) else [],
                'guardado_en': self.datos_clima.guardado_en.isoformat() if self.datos_clima.guardado_en else None,
                'datos_completos': self.datos_clima.datos_completos
            }
        return res
    
    def __repr__(self):
        return f'<Consulta {self.id} - {self.tipo_consulta} - {self.estado}>'
