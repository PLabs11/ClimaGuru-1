"use client";

import { useEffect, useState } from "react";
import {
  History,
  MapPin,
  ChevronDown,
  ChevronUp,
  RefreshCcw,
  Thermometer,
  Droplets,
  Wind,
  Gauge,
  Radio,
  Calendar,
  Layers,
  Database,
  Download,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";
import type { Consulta } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  actual: "Clima Actual",
  tiempo_real: "Clima Actual",
  pronostico: "Pronóstico Extendido",
  historico: "Histórico Oficial IDEAM",
};

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive"> = {
  completada: "default",
  procesando: "secondary",
  pendiente: "secondary",
  error: "destructive",
};

export default function HistorialPage() {
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [filterText, setFilterText] = useState("");

  function loadHistory() {
    setLoading(true);
    api
      .get<{ consultas: Consulta[] }>("/consultas?per_page=50")
      .then((res) => {
        setConsultas(res.consultas || []);
        // Si hay consultas, expandir la más reciente
        if (res.consultas && res.consultas.length > 0) {
          setExpanded(new Set([res.consultas[0].id]));
        }
      })
      .catch((err) => {
        console.error("Error al cargar historial:", err);
        setConsultas([]);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadHistory();
  }, []);

  function toggleExpand(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function formatDate(iso: string) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("es-CO", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const filteredConsultas = consultas.filter((c) => {
    if (!filterText) return true;
    const term = filterText.toLowerCase();
    return (
      (c.ciudad && c.ciudad.toLowerCase().includes(term)) ||
      (c.tipo_consulta && c.tipo_consulta.toLowerCase().includes(term)) ||
      (c.datos_clima?.fuentes && c.datos_clima.fuentes.toLowerCase().includes(term))
    );
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5" /> Almacenamiento MySQL Activo &bull; {consultas.length} Registros
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Historial de Consultas Meteorológicas
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Registros almacenados permanentemente en la base de datos con fuentes integradas (Meteoblue, Meteosource, IDEAM, OpenWeather).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={loadHistory} disabled={loading} className="shadow-sm">
            <RefreshCcw className={`mr-2 h-4 w-4 ${loading ? "animate-spin text-primary" : ""}`} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por ciudad, tipo o fuente (ej: Bogotá, IDEAM, Meteoblue, Meteosource)..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="pl-9 bg-card border-border/60"
        />
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-xs text-muted-foreground">Cargando registros de la base de datos...</p>
        </div>
      ) : filteredConsultas.length === 0 ? (
        <Card className="border-border/50">
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <History className="h-12 w-12 text-muted-foreground/50" />
            <p className="text-base font-semibold text-foreground">
              {filterText ? "No se encontraron consultas para tu búsqueda" : "Aún no hay consultas en la base de datos"}
            </p>
            <p className="text-xs text-muted-foreground max-w-sm">
              Realiza una consulta desde el mapa interactivo para ver los datos guardados aquí automáticamente.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {filteredConsultas.map((c) => {
            const isOpen = expanded.has(c.id);
            const dc = c.datos_clima;
            const raw = (dc?.datos_completos as Record<string, unknown>) || {};
            const estacionesIdeam =
              dc?.estaciones_ideam ||
              (raw.estaciones_ideam as Array<Record<string, unknown>>) ||
              [];
            const historicoDiario =
              dc?.historico_diario ||
              (raw.historico_diario as Array<Record<string, unknown>>) ||
              [];
            const pronostico =
              dc?.pronostico ||
              (raw.pronostico as Array<Record<string, unknown>>) ||
              [];

            // Extraer lista de fuentes
            let fuentesLista: string[] = [];
            if (dc?.fuentes_lista && dc.fuentes_lista.length > 0) {
              fuentesLista = dc.fuentes_lista;
            } else if (dc?.fuentes) {
              fuentesLista = dc.fuentes.split(",").map((s) => s.trim());
            }

            return (
              <Card key={c.id} className="border-border/60 transition-all hover:border-border shadow-sm">
                <CardContent className="p-0">
                  <button
                    type="button"
                    onClick={() => toggleExpand(c.id)}
                    className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-secondary/20"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary">
                        <MapPin className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-base font-semibold text-card-foreground">
                            {c.ciudad || `Coord: ${c.latitud}, ${c.longitud}`}
                          </p>
                          <span className="text-[11px] font-mono text-muted-foreground">
                            #{c.id}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(c.creada_en)} &bull; {c.formato?.toUpperCase() || "JSON"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs font-medium">
                        {TYPE_LABELS[c.tipo_consulta] ?? c.tipo_consulta}
                      </Badge>

                      <Badge
                        variant={STATUS_VARIANT[c.estado] ?? "secondary"}
                        className="text-xs capitalize"
                      >
                        {c.estado}
                      </Badge>

                      {isOpen ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </button>

                  {/* Expanded Detail Panel */}
                  {isOpen && dc && (
                    <div className="border-t border-border/50 px-4 pb-5 pt-4 bg-card/50 flex flex-col gap-4">
                      {/* Sources badges row */}
                      {fuentesLista.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pb-1">
                          <span className="text-xs text-muted-foreground mr-1 flex items-center gap-1 font-medium">
                            <Layers className="h-3.5 w-3.5" /> Fuentes registradas:
                          </span>
                          {fuentesLista.map((f) => {
                            const isIdeam = f.toLowerCase().includes("ideam");
                            const isMeteoblue = f.toLowerCase().includes("meteoblue");
                            const isMeteosource = f.toLowerCase().includes("meteosource");
                            return (
                              <Badge
                                key={f}
                                variant="secondary"
                                className={`text-xs ${
                                  isIdeam
                                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                                    : isMeteoblue
                                    ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                                    : isMeteosource
                                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                                    : "bg-secondary text-secondary-foreground"
                                }`}
                              >
                                {isIdeam && "🇨🇴 "}
                                {f}
                              </Badge>
                            );
                          })}
                        </div>
                      )}

                      {/* Metrics 4-grid */}
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        {dc.temperatura != null && (
                          <div className="flex items-center gap-3 rounded-xl bg-secondary/70 border border-border/40 p-3">
                            <Thermometer className="h-4 w-4 shrink-0 text-chart-3" />
                            <div>
                              <p className="text-[11px] text-muted-foreground">Temperatura</p>
                              <p className="text-base font-bold text-foreground">
                                {dc.temperatura}°C
                              </p>
                            </div>
                          </div>
                        )}

                        {dc.humedad != null && (
                          <div className="flex items-center gap-3 rounded-xl bg-secondary/70 border border-border/40 p-3">
                            <Droplets className="h-4 w-4 shrink-0 text-primary" />
                            <div>
                              <p className="text-[11px] text-muted-foreground">Humedad</p>
                              <p className="text-base font-bold text-foreground">
                                {dc.humedad}%
                              </p>
                            </div>
                          </div>
                        )}

                        {dc.viento_vel != null && (
                          <div className="flex items-center gap-3 rounded-xl bg-secondary/70 border border-border/40 p-3">
                            <Wind className="h-4 w-4 shrink-0 text-accent" />
                            <div>
                              <p className="text-[11px] text-muted-foreground">Viento</p>
                              <p className="text-base font-bold text-foreground">
                                {dc.viento_vel} km/h {dc.viento_dir || ""}
                              </p>
                            </div>
                          </div>
                        )}

                        {dc.presion != null && (
                          <div className="flex items-center gap-3 rounded-xl bg-secondary/70 border border-border/40 p-3">
                            <Gauge className="h-4 w-4 shrink-0 text-chart-4" />
                            <div>
                              <p className="text-[11px] text-muted-foreground">Presión</p>
                              <p className="text-base font-bold text-foreground">
                                {dc.presion} hPa
                              </p>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* IDEAM Stations Subpanel (if any) */}
                      {estacionesIdeam && estacionesIdeam.length > 0 && (
                        <div className="rounded-xl border border-amber-500/25 bg-amber-500/5 p-3.5">
                          <p className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 mb-2">
                            <Radio className="h-3.5 w-3.5" />
                            Estaciones de Monitoreo Oficiales del IDEAM Colombia
                          </p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                            {estacionesIdeam.map((est, i) => (
                              <div
                                key={(est.codigo as string) || i}
                                className="rounded-lg bg-card/80 border border-border/50 p-2.5 text-xs"
                              >
                                <p className="font-semibold text-foreground truncate">
                                  {est.nombre as string}
                                </p>
                                <p className="text-[11px] text-muted-foreground">
                                  {est.departamento as string} &bull; Cód: {est.codigo as string}
                                </p>
                                {est.temperatura_registrada != null && (
                                  <p className="text-xs font-bold text-amber-400 mt-1">
                                    Registrado: {String(est.temperatura_registrada)}°C
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* IDEAM / ERA5 7-day Historical Table (if any) */}
                      {historicoDiario && historicoDiario.length > 0 && (
                        <div className="rounded-xl border border-border/50 overflow-hidden">
                          <div className="bg-secondary/70 px-3 py-2 text-xs font-semibold text-foreground flex items-center gap-1.5">
                            <Calendar className="h-3.5 w-3.5 text-primary" />
                            Historial Diario Registrado en BD (IDEAM / ERA5)
                          </div>
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs text-left">
                              <thead className="bg-secondary/40 text-muted-foreground border-b border-border/40">
                                <tr>
                                  <th className="px-3 py-2">Fecha</th>
                                  <th className="px-3 py-2">Temp Media</th>
                                  <th className="px-3 py-2">Máx / Mín</th>
                                  <th className="px-3 py-2">Precipitación</th>
                                  <th className="px-3 py-2">Viento Máx</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-border/20">
                                {historicoDiario.map((row, i) => (
                                  <tr key={(row.fecha as string) || i}>
                                    <td className="px-3 py-1.5 font-medium">{String(row.fecha)}</td>
                                    <td className="px-3 py-1.5 font-bold text-chart-3">
                                      {row.temperatura_media != null ? `${row.temperatura_media}°C` : "-"}
                                    </td>
                                    <td className="px-3 py-1.5 text-muted-foreground">
                                      {row.temperatura_max != null ? `${row.temperatura_max}°C` : "-"} /{" "}
                                      {row.temperatura_min != null ? `${row.temperatura_min}°C` : "-"}
                                    </td>
                                    <td className="px-3 py-1.5 text-primary">
                                      {row.precipitacion != null ? `${row.precipitacion} mm` : "0 mm"}
                                    </td>
                                    <td className="px-3 py-1.5 text-muted-foreground">
                                      {row.velocidad_viento_max != null ? `${row.velocidad_viento_max} km/h` : "-"}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Pronóstico extendido si existe */}
                      {pronostico && pronostico.length > 0 && (
                        <div className="rounded-xl border border-border/50 p-3 bg-secondary/30">
                          <p className="text-xs font-semibold text-foreground mb-2 flex items-center gap-1.5">
                            <Calendar className="h-3.5 w-3.5 text-primary" />
                            Pronóstico Almacenado (Meteoblue & Meteosource)
                          </p>
                          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-2">
                            {pronostico.slice(0, 5).map((p, i) => (
                              <div key={(p.fecha as string) || i} className="rounded-lg bg-card/60 border border-border/40 p-2 text-xs">
                                <p className="font-semibold text-foreground">
                                  {p.fecha ? String(p.fecha).split("T")[0] : `Día ${i + 1}`}
                                </p>
                                <p className="text-sm font-bold text-chart-3 mt-1">
                                  {p.temperatura != null
                                    ? `${p.temperatura}°C`
                                    : p.temperatura_max != null
                                    ? `${p.temperatura_max}°C`
                                    : "-"}
                                </p>
                                <p className="text-[11px] text-muted-foreground truncate">
                                  {String(p.descripcion || "")}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Footer Actions */}
                      <div className="flex items-center justify-between pt-2 border-t border-border/40 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1.5">
                          <Database className="h-3.5 w-3.5 text-emerald-500" />
                          Guardado en base de datos MySQL: {formatDate(dc.guardado_en)}
                        </span>
                        <a
                          href={`http://localhost:5000/api/consultas/${c.id}/descargar`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                        >
                          <Download className="h-3.5 w-3.5" />
                          Descargar ({c.formato?.toUpperCase() || "JSON"})
                        </a>
                      </div>
                    </div>
                  )}

                  {isOpen && !dc && (
                    <div className="border-t border-border/50 px-4 pb-4 pt-3 text-xs text-muted-foreground">
                      No hay datos meteorológicos asociados guardados para esta consulta.
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
