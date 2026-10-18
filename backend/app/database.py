"""
Configuración y utilidades de la base de datos
===============================================
Módulo para gestionar la conexión y operaciones con la base de datos MySQL
"""

from flask import current_app
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


def test_connection():
    """
    Prueba la conexión a la base de datos
    
    Returns:
        tuple: (bool, str) - (exitoso, mensaje)
    """
    try:
        # Intentar conectar y ejecutar una consulta simple
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✓ Conexión a la base de datos exitosa")
        return True, "Conexión exitosa"
    
    except OperationalError as e:
        error_msg = f"Error de conexión a la base de datos: {str(e)}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg


def get_database_info():
    """
    Obtiene información sobre la base de datos conectada
    
    Returns:
        dict: Información de la base de datos
    """
    try:
        inspector = inspect(db.engine)
        
        info = {
            "database": db.engine.url.database,
            "host": db.engine.url.host,
            "port": db.engine.url.port,
            "driver": db.engine.url.drivername,
            "tables": inspector.get_table_names(),
            "total_tables": len(inspector.get_table_names())
        }
        
        logger.info(f"Base de datos: {info['database']} en {info['host']}:{info['port']}")
        logger.info(f"Total de tablas: {info['total_tables']}")
        
        return info
    
    except Exception as e:
        logger.error(f"Error al obtener información de la BD: {str(e)}")
        return {"error": str(e)}


def get_table_info(tabla_nombre):
    """
    Obtiene información detallada de una tabla específica
    
    Args:
        tabla_nombre (str): Nombre de la tabla
    
    Returns:
        dict: Información de la tabla
    """
    try:
        inspector = inspect(db.engine)
        
        if tabla_nombre not in inspector.get_table_names():
            return {"error": f"La tabla '{tabla_nombre}' no existe"}
        
        columns = inspector.get_columns(tabla_nombre)
        pk = inspector.get_pk_constraint(tabla_nombre)
        indexes = inspector.get_indexes(tabla_nombre)
        foreign_keys = inspector.get_foreign_keys(tabla_nombre)
        
        info = {
            "tabla": tabla_nombre,
            "columnas": [
                {
                    "nombre": col['name'],
                    "tipo": str(col['type']),
                    "nullable": col['nullable'],
                    "default": col.get('default')
                }
                for col in columns
            ],
            "primary_key": pk['constrained_columns'] if pk else [],
            "indexes": [idx['name'] for idx in indexes],
            "foreign_keys": [
                {
                    "columnas": fk['constrained_columns'],
                    "referencia": f"{fk['referred_table']}.{fk['referred_columns']}"
                }
                for fk in foreign_keys
            ]
        }
        
        return info
    
    except Exception as e:
        logger.error(f"Error al obtener info de tabla '{tabla_nombre}': {str(e)}")
        return {"error": str(e)}


def verify_database_schema():
    """
    Verifica que todas las tablas esperadas existan en la base de datos
    
    Returns:
        dict: Estado de las tablas
    """
    expected_tables = [
        'usuarios',
        'api_keys',
        'consultas',
        'datos_clima',
        'sesiones',
        'ciudades_favoritas',
        'logs_actividad',
        'alertas_clima',
        'configuraciones_usuario'
    ]
    
    try:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        result = {
            "total_esperadas": len(expected_tables),
            "total_existentes": len(existing_tables),
            "tablas_encontradas": [],
            "tablas_faltantes": [],
            "tablas_adicionales": []
        }
        
        for table in expected_tables:
            if table in existing_tables:
                result["tablas_encontradas"].append(table)
            else:
                result["tablas_faltantes"].append(table)
        
        for table in existing_tables:
            if table not in expected_tables:
                result["tablas_adicionales"].append(table)
        
        if result["tablas_faltantes"]:
            logger.warning(f"Tablas faltantes: {result['tablas_faltantes']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error al verificar esquema: {str(e)}")
        return {"error": str(e)}


def init_database(app):
    """
    Inicializa la base de datos y verifica la conexión
    
    Args:
        app: Instancia de Flask
    
    Returns:
        bool: True si la inicialización fue exitosa
    """
    with app.app_context():
        try:
            # Verificar conexión
            success, message = test_connection()
            if not success:
                logger.error(f"No se pudo conectar a la base de datos: {message}")
                return False
            
            # Obtener información de la BD
            db_info = get_database_info()
            logger.info(f"Conectado a: {db_info.get('database', 'unknown')}")
            
            # Verificar esquema
            schema_status = verify_database_schema()
            logger.info(f"Tablas encontradas: {schema_status.get('total_existentes', 0)}")
            
            if schema_status.get('tablas_faltantes'):
                try:
                    db.create_all()
                    logger.info("Tablas creadas automáticamente con db.create_all()")
                except Exception as ex:
                    logger.warning(f"No se pudieron auto-crear tablas: {ex}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error al inicializar la base de datos: {str(e)}")
            return False


def execute_raw_query(query, params=None):
    """
    Ejecuta una consulta SQL cruda (usar con precaución)
    
    Args:
        query (str): Consulta SQL
        params (dict, optional): Parámetros para la consulta
    
    Returns:
        list: Resultados de la consulta
    """
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            
            # Si es un SELECT, devolver resultados
            if query.strip().upper().startswith('SELECT'):
                return [dict(row._mapping) for row in result]
            
            # Si es INSERT/UPDATE/DELETE, hacer commit
            connection.commit()
            return {"affected_rows": result.rowcount}
    
    except Exception as e:
        logger.error(f"Error al ejecutar consulta: {str(e)}")
        raise


def truncate_all_tables():
    """
    PELIGRO: Vacía todas las tablas (solo para desarrollo/testing)
    """
    if current_app.config.get('FLASK_ENV') == 'production':
        raise PermissionError("No se permite truncar tablas en producción")
    
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        with db.engine.connect() as connection:
            # Desactivar foreign key checks
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            for table in tables:
                connection.execute(text(f"TRUNCATE TABLE {table}"))
                logger.info(f"Tabla '{table}' vaciada")
            
            # Reactivar foreign key checks
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            connection.commit()
        
        return {"message": f"{len(tables)} tablas vaciadas exitosamente"}
    
    except Exception as e:
        logger.error(f"Error al truncar tablas: {str(e)}")
        raise

