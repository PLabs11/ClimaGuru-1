// ── Modelos de datos (reflejan la BD MySQL) ──────────────────────────

export interface Usuario {
  id: number;
  username: string;
  email: string;
  rol: "admin" | "usuario";
  activo: boolean;
  creado_en: string;
}

export interface Consulta {
  id: number;
  usuario_id: number;
  tipo_consulta: string;
  ciudad: string;
  latitud: number | null;
  longitud: number | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  formato: string;
  parametros: string | null;
  respuesta_api: string | null;
  promedios: string | null;
  estado: string;
  creada_en: string;
  datos_clima?: DatosClima;
}

export interface DatosClima {
  id: number;
  consulta_id: number;
  temperatura: number | null;
  temperatura_min?: number | null;
  temperatura_max?: number | null;
  presion: number | null;
  humedad: number | null;
  viento_vel: number | null;
  viento_dir: string | null;
  precipitacion?: number | null;
  descripcion?: string | null;
  fuentes: string | null;
  fuentes_lista?: string[];
  guardado_en: string;
  pronostico?: Array<{
    fecha: string;
    temperatura?: number | null;
    temperatura_max?: number | null;
    temperatura_min?: number | null;
    humedad?: number | null;
    precipitacion?: number | null;
    velocidad_viento?: number | null;
    descripcion?: string;
  }>;
  historico_diario?: Array<{
    fecha: string;
    temperatura_max?: number | null;
    temperatura_min?: number | null;
    temperatura_media?: number | null;
    precipitacion?: number | null;
    velocidad_viento_max?: number | null;
    humedad_media?: number | null;
    fuente?: string;
  }>;
  estaciones_ideam?: Array<{
    codigo?: string;
    nombre?: string;
    departamento?: string;
    municipio?: string;
    temperatura_registrada?: number | null;
    fecha_observacion?: string;
    sensor?: string;
    fuente?: string;
  }>;
  datos_completos?: Record<string, unknown>;
}

export interface ApiKey {
  id: number;
  usuario_id: number;
  proveedor: string;
  api_key: string;
  activa: boolean;
  creada_en: string;
}

// ── Payloads de autenticacion ────────────────────────────────────────

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  user: Usuario;
}

// ── Dashboard Stats ──────────────────────────────────────────────────

export interface DashboardStats {
  total_consultas: number;
  consultas_hoy: number;
  api_keys_activas: number;
  ciudades_frecuentes: { ciudad: string; count: number }[];
  consultas_por_dia: { fecha: string; count: number }[];
  promedios: {
    temperatura: number;
    humedad: number;
    presion: number;
    viento: number;
  };
}
