"""
CLIMAPI - Sistema Integrado de Consulta de Datos Climáticos
============================================================

Sistema que integra múltiples fuentes de datos meteorológicos:
- Meteoblue: Pronósticos detallados y meteogramas
- Open-Meteo: Pronósticos gratuitos y datos históricos
- OpenWeatherMap: Clima actual, pronóstico 5 días y calidad del aire
- IDEAM: Datos de radares meteorológicos (AWS)
- SIATA: Datos históricos meteorológicos de Medellín y región

Autor: ClimAPI Team
Fecha: Diciembre 2025
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Configurar codificación UTF-8 en Windows para evitar UnicodeEncodeError
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar clientes
from src.data_sources.meteoblue import MeteoblueClient
from src.data_sources.open_meteo import OpenMeteoClient
from src.data_sources.openweather import OpenWeatherMapClient
from src.data_sources.Meteosource import MeteosourceAPI
from src.data_sources.siata_cliente import SIATADownloader
try:
    from src.data_sources.ideam_radar_downloader import IDEAMRadarDownloader
    from src.processors.radar_processor import RadarDataProcessor
except ImportError:
    IDEAMRadarDownloader = None
    RadarDataProcessor = None


class ClimAPIManager:
    """Gestor central de todas las APIs climáticas"""
    
    def __init__(self):
        """Inicializa todos los clientes disponibles"""
        load_dotenv()
        
        # Directorio de datos
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Inicializar clientes
        self.meteoblue = None
        self.openmeteo = None
        self.openweather = None
        self.meteosource = None
        self.ideam_radar = None
        self.siata = None
        self.radar_processor = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializa los clientes de APIs"""
        
        # Meteoblue (requiere API key y secret)
        try:
            meteoblue_key = os.getenv("METEOBLUE_API_KEY")
            meteoblue_secret = os.getenv("METEOBLUE_SHARED_SECRET")
            if meteoblue_key and meteoblue_secret:
                self.meteoblue = MeteoblueClient(meteoblue_key, meteoblue_secret)
                print("✅ Meteoblue inicializado")
            else:
                print("⚠️  Meteoblue: No configurado (requiere API key y secret)")
        except Exception as e:
            print(f"⚠️  Meteoblue: Error al inicializar - {e}")
        
        # Open-Meteo (gratuito, sin API key)
        try:
            self.openmeteo = OpenMeteoClient()
            print("✅ Open-Meteo inicializado")
        except Exception as e:
            print(f"⚠️  Open-Meteo: Error al inicializar - {e}")
        
        # OpenWeatherMap (requiere API key)
        try:
            openweather_key = os.getenv("OPENWEATHER_API_KEY")
            if openweather_key:
                self.openweather = OpenWeatherMapClient(openweather_key)
                print("✅ OpenWeatherMap inicializado")
            else:
                print("⚠️  OpenWeatherMap: No configurado (requiere API key)")
        except Exception as e:
            print(f"⚠️  OpenWeatherMap: Error al inicializar - {e}")
        
        # Meteosource (requiere API key)
        try:
            meteosource_key = os.getenv("METEOSOURCE_API_KEY")
            if meteosource_key:
                self.meteosource = MeteosourceAPI()
                print("✅ Meteosource inicializado")
            else:
                print("⚠️  Meteosource: No configurado (requiere API key)")
        except Exception as e:
            print(f"⚠️  Meteosource: Error al inicializar - {e}")
        
        # IDEAM Radar (AWS público, no requiere credenciales)
        try:
            if IDEAMRadarDownloader and RadarDataProcessor:
                self.ideam_radar = IDEAMRadarDownloader()
                self.radar_processor = RadarDataProcessor()
                print("✅ IDEAM Radar inicializado")
            else:
                print("⚠️  IDEAM Radar: Módulo no disponible (requiere boto3)")
        except Exception as e:
            print(f"⚠️  IDEAM Radar: Error al inicializar - {e}")
        
        # SIATA (público, no requiere credenciales)
        try:
            self.siata = SIATADownloader()
            print("✅ SIATA inicializado")
        except Exception as e:
            print(f"⚠️  SIATA: Error al inicializar - {e}")
    
    def consultar_meteoblue(self, lat, lon, location_name, asl=0):
        """Consulta Meteoblue para una ubicación"""
        if not self.meteoblue:
            print("❌ Meteoblue no está configurado")
            return None
        
        print(f"\n📊 Consultando Meteoblue para {location_name}...")
        try:
            # Obtener pronóstico
            forecast = self.meteoblue.get_forecast(lat, lon, asl, 
                                                   location_name=location_name)
            
            # Obtener meteograma (imagen)
            self.meteoblue.get_meteogram_image(lat, lon, asl, 
                                               location_name=location_name,
                                               lang="es")
            
            print(f"✅ Datos de Meteoblue obtenidos para {location_name}")
            return forecast
        except Exception as e:
            print(f"❌ Error en Meteoblue: {e}")
            return None
    
    def consultar_openmeteo(self, lat, lon, location_name):
        """Consulta Open-Meteo para una ubicación"""
        if not self.openmeteo:
            print("❌ Open-Meteo no está configurado")
            return None
        
        print(f"\n📊 Consultando Open-Meteo para {location_name}...")
        try:
            # Pronóstico 7 días
            forecast = self.openmeteo.get_forecast(lat, lon, 
                                                   location_name=location_name,
                                                   days=7)
            
            print(f"✅ Pronóstico Open-Meteo obtenido para {location_name}")
            return forecast
        except Exception as e:
            print(f"❌ Error en Open-Meteo: {e}")
            return None
    
    def consultar_openmeteo_historico(self, lat, lon, location_name, 
                                     start_date, end_date):
        """Consulta datos históricos de Open-Meteo"""
        if not self.openmeteo:
            print("❌ Open-Meteo no está configurado")
            return None
        
        print(f"\n📊 Consultando datos históricos Open-Meteo para {location_name}...")
        try:
            historical = self.openmeteo.get_historical(lat, lon, 
                                                       start_date, end_date,
                                                       location_name=location_name)
            
            print(f"✅ Datos históricos Open-Meteo obtenidos para {location_name}")
            return historical
        except Exception as e:
            print(f"❌ Error en Open-Meteo histórico: {e}")
            return None
    
    def consultar_openweather(self, lat, lon, location_name):
        """Consulta OpenWeatherMap para una ubicación"""
        if not self.openweather:
            print("❌ OpenWeatherMap no está configurado")
            return None
        
        print(f"\n📊 Consultando OpenWeatherMap para {location_name}...")
        try:
            # Clima actual
            current = self.openweather.get_current_weather(lat, lon, 
                                                          location_name=location_name)
            
            # Pronóstico 5 días
            forecast = self.openweather.get_forecast_5day(lat, lon, 
                                                         location_name=location_name)
            
            # Calidad del aire
            air_quality = self.openweather.get_air_pollution(lat, lon, 
                                                            location_name=location_name)
            
            print(f"✅ Datos OpenWeatherMap obtenidos para {location_name}")
            return {
                "current": current,
                "forecast": forecast,
                "air_quality": air_quality
            }
        except Exception as e:
            print(f"❌ Error en OpenWeatherMap: {e}")
            return None
    
    def consultar_meteosource(self, place_id, location_name=None):
        """Consulta Meteosource para una ubicación"""
        if not self.meteosource:
            print("❌ Meteosource no está configurado")
            return None
        
        if location_name is None:
            location_name = place_id
        
        print(f"\n📊 Consultando Meteosource para {location_name}...")
        try:
            # Obtener todos los datos (current, hourly, daily)
            data = self.meteosource.get_all_data(place_id)
            
            if data:
                # Guardar datos
                self.meteosource.save_data(data, place_id, 'complete')
                
                # Mostrar clima actual
                self.meteosource.display_current_weather(data)
                
                print(f"✅ Datos Meteosource obtenidos para {location_name}")
                return data
            else:
                print(f"❌ No se pudieron obtener datos de Meteosource")
                return None
        except Exception as e:
            print(f"❌ Error en Meteosource: {e}")
            return None
    
    def consultar_ideam_radar(self, radar_name="Barrancabermeja", fecha=None, 
                            limite_archivos=10):
        """Consulta datos de radar IDEAM"""
        if not self.ideam_radar:
            print("❌ IDEAM Radar no está configurado")
            return None
        
        print(f"\n📡 Consultando IDEAM Radar: {radar_name}...")
        try:
            # Listar archivos disponibles
            if fecha is None:
                fecha = datetime.now() - timedelta(days=1)
            
            archivos = self.ideam_radar.listar_archivos_disponibles(
                radar_name, fecha, limite=limite_archivos
            )
            
            print(f"✅ Encontrados {len(archivos)} archivos de radar para {radar_name}")
            return archivos
        except Exception as e:
            print(f"❌ Error en IDEAM Radar: {e}")
            return None
    
    def listar_radares_ideam(self):
        """Lista radares IDEAM disponibles"""
        if not self.ideam_radar:
            print("❌ IDEAM Radar no está configurado")
            return None
        
        return self.ideam_radar.listar_radares()
    
    def descargar_datos_siata(self, max_depth=2):
        """Descarga datos históricos de SIATA"""
        if not self.siata:
            print("❌ SIATA no está configurado")
            return None
        
        print(f"\n🌐 Descargando datos históricos de SIATA...")
        try:
            self.siata.download_all(max_depth=max_depth)
            print(f"✅ Descarga de SIATA completada")
        except Exception as e:
            print(f"❌ Error en SIATA: {e}")
    
    def consulta_completa(self, lat, lon, location_name, asl=0):
        """Realiza una consulta completa a todas las APIs disponibles"""
        print(f"\n{'='*70}")
        print(f"CONSULTA COMPLETA PARA: {location_name}")
        print(f"Coordenadas: {lat}°N, {lon}°W")
        print(f"{'='*70}")
        
        resultados = {
            "location": location_name,
            "coordinates": {"lat": lat, "lon": lon, "asl": asl},
            "timestamp": datetime.now().isoformat(),
            "meteoblue": None,
            "openmeteo": None,
            "openweather": None,
            "meteosource": None
        }
        
        # Meteoblue
        resultados["meteoblue"] = self.consultar_meteoblue(lat, lon, location_name, asl)
        
        # Open-Meteo
        resultados["openmeteo"] = self.consultar_openmeteo(lat, lon, location_name)
        
        # OpenWeatherMap
        resultados["openweather"] = self.consultar_openweather(lat, lon, location_name)
        
        # Meteosource (convertir nombre a place_id)
        place_id = location_name.lower().replace(' ', '_').replace('í', 'i').replace('ó', 'o').replace('á', 'a')
        resultados["meteosource"] = self.consultar_meteosource(place_id, location_name)
        
        # Guardar resumen
        self._guardar_resumen_consulta(resultados)
        
        return resultados
    
    def _guardar_resumen_consulta(self, resultados):
        """Guarda un resumen de la consulta completa"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consulta_completa_{resultados['location']}_{timestamp}.json"
        filepath = self.data_dir / filename
        
        # Preparar datos para JSON (convertir DataFrames si existen)
        resultados_json = resultados.copy()
        
        # Open-Meteo tiene DataFrames que no son serializables
        if resultados_json.get("openmeteo"):
            if resultados_json["openmeteo"].get("daily") is not None:
                resultados_json["openmeteo"]["daily"] = "Datos guardados en CSV"
            if resultados_json["openmeteo"].get("hourly") is not None:
                resultados_json["openmeteo"]["hourly"] = "Datos guardados en CSV"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(resultados_json, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Resumen guardado en: {filepath}")


def menu_principal():
    """Menú principal interactivo"""
    manager = ClimAPIManager()
    
    # Ubicaciones predefinidas de Colombia
    ubicaciones = {
        "1": {"name": "Medellin", "lat": 6.245, "lon": -75.5715, "asl": 1495},
        "2": {"name": "Bogota", "lat": 4.711, "lon": -74.0721, "asl": 2640},
        "3": {"name": "Cartagena", "lat": 10.391, "lon": -75.4794, "asl": 2},
        "4": {"name": "Cali", "lat": 3.4516, "lon": -76.532, "asl": 995},
        "5": {"name": "Barranquilla", "lat": 10.9639, "lon": -74.7964, "asl": 18},
    }
    
    while True:
        print("\n" + "="*70)
        print("CLIMAPI - Sistema de Consulta de Datos Climáticos")
        print("="*70)
        print("\n1. Consulta completa (todas las APIs)")
        print("2. Consultar solo Meteoblue")
        print("3. Consultar solo Open-Meteo (pronóstico)")
        print("4. Consultar solo Open-Meteo (histórico)")
        print("5. Consultar solo OpenWeatherMap")
        print("6. Consultar solo Meteosource")
        print("7. Consultar radares IDEAM")
        print("8. Listar radares IDEAM disponibles")
        print("9. Descargar datos SIATA históricos")
        print("10. Salir")
        
        opcion = input("\nSeleccione una opción: ").strip()
        
        if opcion == "10":
            print("\n👋 ¡Hasta luego!")
            break
        
        if opcion in ["1", "2", "3", "4", "5", "6"]:
            # Seleccionar ubicación
            print("\nUbicaciones disponibles:")
            for key, loc in ubicaciones.items():
                print(f"{key}. {loc['name']}")
            print("6. Ingresar coordenadas manualmente")
            
            loc_opcion = input("\nSeleccione ubicación: ").strip()
            
            if loc_opcion in ubicaciones:
                loc = ubicaciones[loc_opcion]
                lat, lon, name, asl = loc["lat"], loc["lon"], loc["name"], loc["asl"]
            elif loc_opcion == "6":
                name = input("Nombre de ubicación: ").strip()
                lat = float(input("Latitud: ").strip())
                lon = float(input("Longitud: ").strip())
                asl = int(input("Altitud (metros): ").strip() or "0")
            else:
                print("❌ Opción inválida")
                continue
            
            # Ejecutar consulta según opción
            if opcion == "1":
                manager.consulta_completa(lat, lon, name, asl)
            elif opcion == "2":
                manager.consultar_meteoblue(lat, lon, name, asl)
            elif opcion == "3":
                manager.consultar_openmeteo(lat, lon, name)
            elif opcion == "4":
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=14)
                manager.consultar_openmeteo_historico(
                    lat, lon, name,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
            elif opcion == "5":
                manager.consultar_openweather(lat, lon, name)
            elif opcion == "6":
                # Meteosource usa place_id en lugar de coordenadas
                place_id = name.lower().replace(' ', '_').replace('í', 'i').replace('ó', 'o').replace('á', 'a')
                manager.consultar_meteosource(place_id, name)
        
        elif opcion == "7":
            # Radares IDEAM
            print("\nRadares disponibles:")
            print("1. Barrancabermeja (más cercano a Medellín)")
            print("2. Guaviare")
            print("3. Munchique")
            print("4. Carimagua")
            
            radar_opcion = input("\nSeleccione radar: ").strip()
            radares_map = {
                "1": "Barrancabermeja",
                "2": "Guaviare",
                "3": "Munchique",
                "4": "Carimagua"
            }
            
            radar_name = radares_map.get(radar_opcion, "Barrancabermeja")
            manager.consultar_ideam_radar(radar_name)
        
        elif opcion == "8":
            manager.listar_radares_ideam()
        
        elif opcion == "9":
            profundidad = input("Profundidad de exploración (1-3, default=2): ").strip()
            profundidad = int(profundidad) if profundidad else 2
            manager.descargar_datos_siata(max_depth=profundidad)
        
        else:
            print("❌ Opción inválida")
        
        input("\nPresione ENTER para continuar...")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                          CLIMAPI                              ║
    ║         Sistema Integrado de Datos Climáticos                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    menu_principal()
