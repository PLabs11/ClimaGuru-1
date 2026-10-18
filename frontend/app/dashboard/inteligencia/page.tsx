"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Sprout,
  Plane,
  Truck,
  ShieldAlert,
  Sun,
  Wind,
  Zap,
  CloudRain,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Compass,
  Layers,
  Info,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api-client";

const CIUDADES_RAPIDAS = ["Medellín", "Bogotá", "Cali", "Barranquilla", "Cartagena"];

export default function InteligenciaPage() {
  const [ciudad, setCiudad] = useState("Medellín");
  const [busqueda, setBusqueda] = useState("Medellín");
  const [loading, setLoading] = useState(false);

  // Estados de datos
  const [decisionData, setDecisionData] = useState<any>(null);
  const [nowcastingData, setNowcastingData] = useState<any>(null);
  const [energyData, setEnergyData] = useState<any>(null);
  const [nmmData, setNmmData] = useState<any>(null);

  // Parámetros de simulación energética
  const [solarKwp, setSolarKwp] = useState<number>(5.0);
  const [eolicaKw, setEolicaKw] = useState<number>(10.0);
  const [dominioNmm, setDominioNmm] = useState<string>("NMM18");

  async function cargarTodo(nombreCiudad: string) {
    setLoading(true);
    setCiudad(nombreCiudad);
    try {
      // 1. Asistente de Decisión
      const dec = await api.post<any>("/consultas/analisis-decision", {
        ciudad: nombreCiudad,
        sector: "todos",
      });
      setDecisionData(dec);

      // 2. Nowcasting Gratuito
      const now = await api.get<any>(`/consultas/nowcasting?ciudad=${encodeURIComponent(nombreCiudad)}`);
      setNowcastingData(now);

      // 3. Energía Renovable Gratuita
      const ene = await api.get<any>(
        `/consultas/energia-renovable?ciudad=${encodeURIComponent(nombreCiudad)}&solar_kwp=${solarKwp}&eolica_kw=${eolicaKw}`
      );
      setEnergyData(ene);

      // 4. Meteoblue NMM18 Dataset
      const nmm = await api.post<any>("/consultas/meteoblue/nmm", {
        ciudad: nombreCiudad,
        dominio: dominioNmm,
      });
      setNmmData(nmm);
    } catch (err) {
      console.error("Error al cargar inteligencia meteorológica:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    cargarTodo(ciudad);
  }, []);

  function handleBuscar(e: React.FormEvent) {
    e.preventDefault();
    if (busqueda.trim()) {
      cargarTodo(busqueda.trim());
    }
  }

  const sec = decisionData?.analisis_sectorial;
  const met = decisionData?.metricas_meteorologicas;

  return (
    <div className="flex flex-col gap-6">
      {/* Encabezado */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Cerebro Analítico & Asistente IA
            </h1>
            <Badge className="bg-primary/20 text-primary border-primary/40 flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> Capa Cognitiva
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Toma de decisiones sectoriales, nowcasting minuto a minuto y predicción de energía 100% gratuita.
          </p>
        </div>

        {/* Buscador de Ciudad */}
        <form onSubmit={handleBuscar} className="flex items-center gap-2">
          <Input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar ciudad..."
            className="w-48 sm:w-64"
          />
          <Button type="submit" disabled={loading} size="sm">
            <Search className="h-4 w-4 mr-1" /> {loading ? "Analizando..." : "Consultar"}
          </Button>
        </form>
      </div>

      {/* Selector de ciudades rápidas */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground font-medium">Ciudades rápidas:</span>
        {CIUDADES_RAPIDAS.map((c) => (
          <Button
            key={c}
            variant={ciudad === c ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs"
            onClick={() => {
              setBusqueda(c);
              cargarTodo(c);
            }}
          >
            {c}
          </Button>
        ))}
      </div>

      {/* Dictamen Ejecutivo Principal */}
      {decisionData && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-primary/20 p-2 text-primary mt-0.5">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                  Dictamen Ejecutivo del Asistente Inteligente • {ciudad}
                </p>
                <p className="text-sm font-medium text-foreground mt-1">
                  {decisionData.dictamen_ejecutivo_ia}
                </p>
                <div className="flex flex-wrap gap-4 mt-2 text-xs text-muted-foreground">
                  <span>Temp: <strong>{met?.temperatura_c}°C</strong></span>
                  <span>Humedad: <strong>{met?.humedad_porcentaje}%</strong></span>
                  <span>Viento: <strong>{met?.viento_kmh} km/h</strong></span>
                  <span>Punto Rocío: <strong>{met?.punto_rocio_c}°C</strong></span>
                  <span>Techo de Nubes: <strong>{met?.techo_nubes_estimado_ft} ft</strong></span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pestañas Principales */}
      <Tabs defaultValue="decisiones" className="w-full">
        <TabsList className="grid grid-cols-2 md:grid-cols-4 w-full">
          <TabsTrigger value="decisiones" className="flex items-center gap-1.5">
            <Sparkles className="h-4 w-4" /> Toma de Decisiones
          </TabsTrigger>
          <TabsTrigger value="nowcasting" className="flex items-center gap-1.5">
            <CloudRain className="h-4 w-4" /> Nowcasting 2 Horas
          </TabsTrigger>
          <TabsTrigger value="energia" className="flex items-center gap-1.5">
            <Zap className="h-4 w-4" /> Energía Renovable
          </TabsTrigger>
          <TabsTrigger value="nmm" className="flex items-center gap-1.5">
            <Layers className="h-4 w-4" /> Modelo NMM18
          </TabsTrigger>
        </TabsList>

        {/* ========================================================= */}
        {/* TAB 1: TOMA DE DECISIONES SECTORIALES                     */}
        {/* ========================================================= */}
        <TabsContent value="decisiones" className="space-y-4 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 1. Agricultura */}
            <Card className="border-emerald-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <Sprout className="h-5 w-5" />
                    <CardTitle className="text-lg">Agricultura de Precisión</CardTitle>
                  </div>
                  <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10">
                    Viabilidad: {sec?.agricultura?.indice_viabilidad_labores || "--"}
                  </Badge>
                </div>
                <CardDescription>Evaluación de fumigación, heladas y régimen hídrico</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Ventana de Fumigación:</span>
                  <Badge className={sec?.agricultura?.ventana_fumigacion_optima ? "bg-emerald-600" : "bg-destructive"}>
                    {sec?.agricultura?.ventana_fumigacion_optima ? "Óptima (Viento y clima favorables)" : "No recomendada"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Alerta de Helada:</span>
                  <span className="font-medium text-foreground">{sec?.agricultura?.alerta_helada || "--"}</span>
                </div>
                <div className="space-y-1.5 pt-1">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">Recomendaciones:</span>
                  {sec?.agricultura?.recomendaciones?.map((r: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 2. Aviación */}
            <Card className="border-sky-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sky-400">
                    <Plane className="h-5 w-5" />
                    <CardTitle className="text-lg">Aviación & Operaciones Aéreas</CardTitle>
                  </div>
                  <Badge variant="outline" className="border-sky-500/40 text-sky-400 bg-sky-500/10">
                    {sec?.aviacion?.categoria_operacional?.split(" ")[0] || "VFR"}
                  </Badge>
                </div>
                <CardDescription>Reglas VFR/IFR, techo de nubes y turbulencia</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Categoría OACI/FAA:</span>
                  <span className="font-semibold text-sky-300">{sec?.aviacion?.categoria_operacional || "--"}</span>
                </div>
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Techo de Nubes AGL:</span>
                  <span className="font-medium text-foreground">{sec?.aviacion?.techo_nuboso_agl || "--"}</span>
                </div>
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Viento en Superficie:</span>
                  <span className="font-medium text-foreground">{sec?.aviacion?.viento_superficie_nudos || "--"} nudos</span>
                </div>
                <div className="space-y-1.5 pt-1">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">Recomendaciones:</span>
                  {sec?.aviacion?.recomendaciones?.map((r: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                      <CheckCircle2 className="h-3.5 w-3.5 text-sky-400 mt-0.5 shrink-0" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 3. Logística y Transporte */}
            <Card className="border-amber-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-amber-400">
                    <Truck className="h-5 w-5" />
                    <CardTitle className="text-lg">Logística & Rutas Terrestres</CardTitle>
                  </div>
                  <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/10">
                    {sec?.logistica?.estado_corredor_vial || "Normal"}
                  </Badge>
                </div>
                <CardDescription>Hidroplaneo, viento cruzado y estimación de retrasos</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Tiempo de Ruta:</span>
                  <span className="font-medium text-foreground">{sec?.logistica?.impacto_en_tiempos_entrega || "--"}</span>
                </div>
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Alerta Hidroplaneo:</span>
                  <span className={sec?.logistica?.riesgo_hidroplaneo_en_calzada ? "text-amber-400 font-semibold" : "text-muted-foreground"}>
                    {sec?.logistica?.riesgo_hidroplaneo_en_calzada ? "Riesgo en calzada" : "Superficie seca"}
                  </span>
                </div>
                <div className="space-y-1.5 pt-1">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">Recomendaciones:</span>
                  {sec?.logistica?.recomendaciones?.map((r: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                      <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 mt-0.5 shrink-0" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 4. Gestión del Riesgo */}
            <Card className="border-red-500/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-red-400">
                    <ShieldAlert className="h-5 w-5" />
                    <CardTitle className="text-lg">Gestión del Riesgo & Protección Civil</CardTitle>
                  </div>
                  <Badge
                    style={{ backgroundColor: `${sec?.gestion_riesgo?.codigo_color}25`, color: sec?.gestion_riesgo?.codigo_color }}
                    className="border"
                  >
                    {sec?.gestion_riesgo?.semaforo_alerta?.split(" ")[0] || "VERDE"}
                  </Badge>
                </div>
                <CardDescription>Alertas tempranas, crecientes súbitas y vendavales</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Semáforo de Alerta:</span>
                  <span className="font-bold" style={{ color: sec?.gestion_riesgo?.codigo_color }}>
                    {sec?.gestion_riesgo?.semaforo_alerta || "--"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/50">
                  <span className="text-muted-foreground">Crecientes Súbitas:</span>
                  <span className={sec?.gestion_riesgo?.riesgo_crecientes_subitas ? "text-red-400 font-semibold" : "text-muted-foreground"}>
                    {sec?.gestion_riesgo?.riesgo_crecientes_subitas ? "Amenaza activa" : "Caudales normales"}
                  </span>
                </div>
                <div className="space-y-1.5 pt-1">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">Recomendaciones:</span>
                  {sec?.gestion_riesgo?.recomendaciones?.map((r: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                      <CheckCircle2 className="h-3.5 w-3.5 text-red-400 mt-0.5 shrink-0" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 2: NOWCASTING GRATUITO (2 HORAS MINUTO A MINUTO)      */}
        {/* ========================================================= */}
        <TabsContent value="nowcasting" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CloudRain className="h-5 w-5 text-sky-400" />
                    Nowcasting Minuto a Minuto (Próximas 2 Horas)
                    <Badge variant="secondary" className="bg-emerald-500/15 text-emerald-400 text-xs">
                      100% Gratuito (Reemplaza Meteosource Premium)
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    Asimilación rápida de radares Doppler meteorológicos sin costo de suscripción
                  </CardDescription>
                </div>
                <Badge variant="outline" className="border-sky-500/40 text-sky-400">
                  {nowcastingData?.radar_cobertura?.proveedor || "Red Doppler Activa"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Mensaje de Resumen */}
              <div className="rounded-lg bg-secondary/50 p-4 border border-border">
                <p className="text-sm font-medium text-foreground">
                  {nowcastingData?.resumen?.mensaje || "Cargando datos de reflectividad de radar..."}
                </p>
              </div>

              {/* Timeline de 15 min */}
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2">
                {nowcastingData?.proyeccion_minutos?.map((p: any, i: number) => (
                  <div
                    key={i}
                    className={`rounded-lg p-3 text-center border flex flex-col items-center justify-between ${
                      p.precipitacion_mm > 0.1
                        ? "bg-sky-500/15 border-sky-500/40"
                        : "bg-background border-border/60"
                    }`}
                  >
                    <span className="text-xs font-bold text-foreground">{p.minuto_relativo}</span>
                    <span className="text-[10px] text-muted-foreground mt-1">
                      {p.hora_estimada?.split("T")[1] || "--"}
                    </span>
                    <div className="my-2 text-center">
                      <span className="text-lg font-bold text-sky-400">{p.precipitacion_mm}</span>
                      <span className="text-[10px] text-muted-foreground block">mm</span>
                    </div>
                    <Badge variant="outline" className="text-[9px] py-0 px-1 border-sky-500/30">
                      {p.probabilidad_porcentaje}% prob
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 3: PREDICCIÓN DE ENERGÍA RENOVABLE (SOLAR Y EÓLICA)   */}
        {/* ========================================================= */}
        <TabsContent value="energia" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="h-5 w-5 text-amber-400" />
                    Modelos de Estimación de Energía Solar & Eólica (kWh)
                    <Badge variant="secondary" className="bg-emerald-500/15 text-emerald-400 text-xs">
                      Modelos Físicos IEC 61724 (Gratis)
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    Predicción horaria de potencia para arreglos fotovoltaicos y turbinas eólicas
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Tarjetas de Totales */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card className="border-amber-500/30 bg-amber-500/5">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-amber-400">ENERGÍA SOLAR (24h)</span>
                      <Sun className="h-4 w-4 text-amber-400" />
                    </div>
                    <p className="text-2xl font-bold text-foreground mt-2">
                      {energyData?.totales_24h?.energia_solar_total_kwh || 0} <span className="text-sm font-normal text-muted-foreground">kWh</span>
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      HSP estimada: <strong>{energyData?.totales_24h?.horas_sol_pico_estimadas_hsp || 0} horas</strong>
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-cyan-500/30 bg-cyan-500/5">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-cyan-400">ENERGÍA EÓLICA (24h)</span>
                      <Wind className="h-4 w-4 text-cyan-400" />
                    </div>
                    <p className="text-2xl font-bold text-foreground mt-2">
                      {energyData?.totales_24h?.energia_eolica_total_kwh || 0} <span className="text-sm font-normal text-muted-foreground">kWh</span>
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Turbina nominal: <strong>{eolicaKw} kW</strong>
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-primary/30 bg-primary/5">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-primary">RENOVABLE COMBINADA</span>
                      <Zap className="h-4 w-4 text-primary" />
                    </div>
                    <p className="text-2xl font-bold text-foreground mt-2">
                      {energyData?.totales_24h?.energia_renovable_combinada_kwh || 0} <span className="text-sm font-normal text-muted-foreground">kWh</span>
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Total limpio estimado en 24 horas
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Curva Horaria Muestra */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-muted-foreground uppercase">
                  Curva de Generación Horaria (Próximas horas):
                </span>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border border-border">
                    <thead className="bg-secondary/60 text-muted-foreground border-b border-border">
                      <tr>
                        <th className="p-2">Hora</th>
                        <th className="p-2">Irradiancia</th>
                        <th className="p-2">Viento (m/s)</th>
                        <th className="p-2">Solar (kWh)</th>
                        <th className="p-2">Eólica (kWh)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {energyData?.curva_horaria_24h?.slice(0, 8).map((row: any, idx: number) => (
                        <tr key={idx} className="border-b border-border/40 hover:bg-secondary/30">
                          <td className="p-2 font-medium">{row.hora?.split("T")[1]}</td>
                          <td className="p-2">{row.irradiancia_w_m2} W/m²</td>
                          <td className="p-2">{row.viento_m_s} m/s</td>
                          <td className="p-2 font-semibold text-amber-400">{row.generacion_solar_kwh}</td>
                          <td className="p-2 font-semibold text-cyan-400">{row.generacion_eolica_kwh}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 4: MODELO NMM METEOBLUE                               */}
        {/* ========================================================= */}
        <TabsContent value="nmm" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Layers className="h-5 w-5 text-blue-400" />
                    Dataset API - Modelo Mesoescalar NMM18 / NEMSAUTO
                  </CardTitle>
                  <CardDescription>
                    Consulta directa de grillas numéricas de alta resolución de Meteoblue
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-blue-500/40 text-blue-400">
                    Dominio: {dominioNmm}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg bg-secondary/40 p-4 border border-border text-xs space-y-2">
                <p>
                  <strong>Fuente:</strong> {nmmData?.fuente || "Meteoblue Dataset API"}
                </p>
                <p>
                  <strong>Resolución espacial:</strong> 18 km para el dominio Suramérica (NMM18)
                </p>
                {nmmData?.aviso && (
                  <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-start gap-2">
                    <Info className="h-4 w-4 mt-0.5 shrink-0" />
                    <span>{nmmData.aviso}</span>
                  </div>
                )}
                {nmmData?.datos && (
                  <pre className="p-2 rounded bg-black/50 text-[10px] overflow-x-auto max-h-48 text-emerald-400">
                    {JSON.stringify(nmmData.datos, null, 2)}
                  </pre>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
