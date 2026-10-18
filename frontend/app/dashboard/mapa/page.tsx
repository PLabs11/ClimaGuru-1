"use client";

import React, { useState } from "react";
import {
  Cloud,
  Search,
  Thermometer,
  Droplets,
  Wind,
  Gauge,
  Calendar,
  Radio,
  Database,
  CheckCircle2,
  Sparkles,
  Info,
  MapPin,
  Clock,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WeatherMap } from "@/components/weather-map";
import { api } from "@/lib/api-client";
import type { Consulta, DatosClima } from "@/lib/types";

interface WeatherResult {
  consulta: Consulta;
  datos?: Record<string, unknown>;
  datos_clima?: DatosClima;
}

export default function MapaPage() {
  const [ciudad, setCiudad] = useState("");
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [tipo, setTipo] = useState("actual");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WeatherResult | null>(null);
  const [error, setError] = useState("");

  function handleMapClick(latitude: number, longitude: number) {
    setLat(latitude);
    setLng(longitude);
    setCiudad("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const payload: Record<string, unknown> = {
        tipo_consulta: tipo,
        formato: "json",
      };

      if (ciudad.trim()) {
        payload.ciudad = ciudad.trim();
      } else if (lat !== null && lng !== null) {
        payload.latitud = lat;
        payload.longitud = lng;
      } else {
        setError("Selecciona una ubicación en el mapa o escribe una ciudad");
        setLoading(false);
        return;
      }

      const data = await api.post<WeatherResult>("/consultas", payload);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error al consultar el clima"
      );
    } finally {
      setLoading(false);
    }
  }

  const dc = result?.datos_clima;
  const fuentesLista = dc?.fuentes_lista || (dc?.fuentes ? dc.fuentes.split(",").map((s) => s.trim()) : []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          Mapa Interactivo & Consulta Multi-Fuente
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Integra datos de <strong className="text-foreground">Meteoblue</strong>,{" "}
          <strong className="text-foreground">Meteosource</strong>,{" "}
          <strong className="text-foreground">IDEAM Colombia</strong> y{" "}
          <strong className="text-foreground">OpenWeatherMap</strong> con almacenamiento automático en MySQL.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Map */}
        <Card className="border-border/50 lg:col-span-2 overflow-hidden shadow-sm">
          <CardContent className="p-0 overflow-hidden rounded-lg">
            <WeatherMap
              onLocationSelect={handleMapClick}
              selectedLat={lat}
              selectedLng={lng}
            />
          </CardContent>
        </Card>

        {/* Query form */}
        <div className="flex flex-col gap-4">
          <Card className="border-border/50 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-card-foreground">
                <Search className="h-4 w-4 text-primary" />
                Consulta de Clima
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="ciudad">Ciudad o Región</Label>
                  <Input
                    id="ciudad"
                    value={ciudad}
                    onChange={(e) => {
                      setCiudad(e.target.value);
                      if (e.target.value) {
                        setLat(null);
                        setLng(null);
                      }
                    }}
                    placeholder="Ej: Bogotá, Medellín, Cali, Barranquilla..."
                  />
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {[
                      { name: "Bogotá", lat: 4.711, lng: -74.0721 },
                      { name: "Medellín", lat: 6.2442, lng: -75.5812 },
                      { name: "Cali", lat: 3.4516, lng: -76.532 },
                      { name: "Cartagena", lat: 10.391, lng: -75.4794 },
                      { name: "Bucaramanga", lat: 7.1254, lng: -73.1198 },
                    ].map((c) => (
                      <button
                        key={c.name}
                        type="button"
                        onClick={() => {
                          setCiudad(c.name);
                          setLat(c.lat);
                          setLng(c.lng);
                        }}
                        className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                          ciudad === c.name
                            ? "bg-primary text-primary-foreground shadow-sm"
                            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                        }`}
                      >
                        {c.name}
                      </button>
                    ))}
                  </div>
                </div>

                {lat !== null && lng !== null && (
                  <div className="rounded-lg bg-secondary/70 border border-border/50 px-3 py-2 text-xs text-secondary-foreground flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-primary" />
                      Coord: {lat.toFixed(4)}, {lng.toFixed(4)}
                    </span>
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  <Label>Tipo de consulta</Label>
                  <Select value={tipo} onValueChange={setTipo}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="actual">Clima actual (Multi-API)</SelectItem>
                      <SelectItem value="pronostico">Pronóstico extendido</SelectItem>
                      <SelectItem value="historico">Histórico Oficial IDEAM / ERA5</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {error && (
                  <div className="rounded-lg bg-destructive/15 border border-destructive/30 p-3 text-xs text-destructive">
                    {error}
                  </div>
                )}

                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                      Consultando APIs & Guardando...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Cloud className="h-4 w-4" />
                      Consultar y Guardar
                    </span>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Status Banner when queried */}
          {result && (
            <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
              <span>
                Consulta registrada con éxito en la base de datos MySQL (ID #{result.consulta.id})
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Results Display */}
      {result && dc && (
        <div className="flex flex-col gap-6">
          {/* Top Summary Card */}
          <Card className="border-border/60 bg-gradient-to-r from-card via-card to-primary/5 shadow-md">
            <CardHeader className="pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-xl font-bold text-card-foreground">
                      {result.consulta.ciudad || "Ubicación Seleccionada"}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs uppercase tracking-wider">
                      {result.consulta.tipo_consulta}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {dc.descripcion || "Condiciones meteorológicas agregadas"}
                  </p>
                </div>

                {/* Badges for sources used */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs text-muted-foreground mr-1 flex items-center gap-1">
                    <Layers className="h-3.5 w-3.5" /> Fuentes:
                  </span>
                  {fuentesLista.map((f) => {
                    const isIdeam = f.toLowerCase().includes("ideam");
                    const isMeteoblue = f.toLowerCase().includes("meteoblue");
                    const isMeteosource = f.toLowerCase().includes("meteosource");
                    return (
                      <Badge
                        key={f}
                        variant="secondary"
                        className={`text-xs font-medium ${
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
              </div>
            </CardHeader>

            <CardContent>
              {/* Primary Metrics Grid */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 pt-1">
                {dc.temperatura != null && (
                  <div className="flex items-center gap-3 rounded-xl bg-secondary/80 border border-border/40 p-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-chart-3/15">
                      <Thermometer className="h-5 w-5 text-chart-3" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground font-medium">Temperatura</p>
                      <p className="text-lg font-bold text-secondary-foreground">
                        {dc.temperatura}°C
                      </p>
                      {dc.temperatura_min != null && dc.temperatura_max != null && (
                        <p className="text-[11px] text-muted-foreground">
                          {dc.temperatura_min}°C / {dc.temperatura_max}°C
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {dc.humedad != null && (
                  <div className="flex items-center gap-3 rounded-xl bg-secondary/80 border border-border/40 p-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                      <Droplets className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground font-medium">Humedad</p>
                      <p className="text-lg font-bold text-secondary-foreground">
                        {dc.humedad}%
                      </p>
                      <p className="text-[11px] text-muted-foreground">Humedad relativa</p>
                    </div>
                  </div>
                )}

                {dc.viento_vel != null && (
                  <div className="flex items-center gap-3 rounded-xl bg-secondary/80 border border-border/40 p-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                      <Wind className="h-5 w-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground font-medium">Viento</p>
                      <p className="text-lg font-bold text-secondary-foreground">
                        {dc.viento_vel} km/h
                      </p>
                      <p className="text-[11px] text-muted-foreground">
                        {dc.viento_dir ? `Dirección ${dc.viento_dir}` : "Velocidad media"}
                      </p>
                    </div>
                  </div>
                )}

                {dc.presion != null && (
                  <div className="flex items-center gap-3 rounded-xl bg-secondary/80 border border-border/40 p-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-chart-4/15">
                      <Gauge className="h-5 w-5 text-chart-4" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground font-medium">Presión</p>
                      <p className="text-lg font-bold text-secondary-foreground">
                        {dc.presion} hPa
                      </p>
                      <p className="text-[11px] text-muted-foreground">Atmosférica</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* IDEAM SECTION (Official Colombia Stations & ERA5 Reanalysis) */}
          {((dc.estaciones_ideam && dc.estaciones_ideam.length > 0) ||
            (dc.historico_diario && dc.historico_diario.length > 0)) && (
            <Card className="border-amber-500/30 bg-gradient-to-br from-card to-amber-500/5 shadow-md">
              <CardHeader className="pb-3 border-b border-border/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/15 text-base">
                      🇨🇴
                    </span>
                    <div>
                      <CardTitle className="text-base font-bold text-foreground">
                        Datos Oficiales IDEAM Colombia
                      </CardTitle>
                      <p className="text-xs text-muted-foreground">
                        Red Nacional de Monitoreo Hidrometeorológico (datos.gov.co) & Reanálisis ERA5
                      </p>
                    </div>
                  </div>
                  <Badge variant="secondary" className="bg-amber-500/15 text-amber-400 border border-amber-500/30">
                    IDEAM Activo
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="pt-4 flex flex-col gap-4">
                {/* Estaciones Oficiales IDEAM */}
                {dc.estaciones_ideam && dc.estaciones_ideam.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Radio className="h-3.5 w-3.5 text-amber-400" />
                      Estaciones Meteorológicas de Monitoreo Cercanas
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                      {dc.estaciones_ideam.map((est, i) => (
                        <div
                          key={est.codigo || i}
                          className="rounded-xl border border-border/60 bg-secondary/50 p-3 flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-mono text-amber-400 font-semibold">
                                Cód: {est.codigo || "IDEAM"}
                              </span>
                              <Badge variant="outline" className="text-[10px] py-0">
                                {est.departamento || "Colombia"}
                              </Badge>
                            </div>
                            <p className="text-sm font-semibold text-foreground mt-1">
                              {est.nombre}
                            </p>
                            {est.municipio && (
                              <p className="text-xs text-muted-foreground">
                                Mun: {est.municipio}
                              </p>
                            )}
                          </div>
                          <div className="mt-2.5 pt-2 border-t border-border/40 flex items-center justify-between">
                            <span className="text-xs text-muted-foreground">
                              {est.sensor || "Sensor de Temp"}
                            </span>
                            {est.temperatura_registrada != null && (
                              <span className="text-sm font-bold text-amber-400">
                                {est.temperatura_registrada}°C
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Historico diario ERA5 / IDEAM */}
                {dc.historico_diario && dc.historico_diario.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-primary" />
                      Historial de los Últimos 7 Días (Reanálisis de Alta Resolución)
                    </h4>
                    <div className="overflow-x-auto rounded-xl border border-border/50">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-secondary/80 text-muted-foreground border-b border-border/50">
                          <tr>
                            <th className="px-3 py-2">Fecha</th>
                            <th className="px-3 py-2">Temp Media</th>
                            <th className="px-3 py-2">Máx / Mín</th>
                            <th className="px-3 py-2">Precipitación</th>
                            <th className="px-3 py-2">Viento Máx</th>
                            <th className="px-3 py-2">Humedad</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/30">
                          {dc.historico_diario.map((row) => (
                            <tr key={row.fecha} className="hover:bg-secondary/30 transition-colors">
                              <td className="px-3 py-2 font-medium text-foreground">{row.fecha}</td>
                              <td className="px-3 py-2 font-semibold text-chart-3">
                                {row.temperatura_media != null ? `${row.temperatura_media}°C` : "-"}
                              </td>
                              <td className="px-3 py-2 text-muted-foreground">
                                {row.temperatura_max != null ? `${row.temperatura_max}°C` : "-"} /{" "}
                                {row.temperatura_min != null ? `${row.temperatura_min}°C` : "-"}
                              </td>
                              <td className="px-3 py-2 text-primary">
                                {row.precipitacion != null ? `${row.precipitacion} mm` : "0 mm"}
                              </td>
                              <td className="px-3 py-2 text-muted-foreground">
                                {row.velocidad_viento_max != null ? `${row.velocidad_viento_max} km/h` : "-"}
                              </td>
                              <td className="px-3 py-2 text-muted-foreground">
                                {row.humedad_media != null ? `${row.humedad_media}%` : "-"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Forecast Days (if pronostico) */}
          {dc.pronostico && dc.pronostico.length > 0 && (
            <Card className="border-border/50 shadow-md">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base font-bold text-card-foreground">
                  <Calendar className="h-4 w-4 text-primary" />
                  Pronóstico Extendido de 5 a 7 Días (Meteoblue & Meteosource)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {dc.pronostico.slice(0, 7).map((p, i) => (
                    <div
                      key={p.fecha || i}
                      className="rounded-xl border border-border/50 bg-secondary/50 p-3.5 flex flex-col justify-between"
                    >
                      <p className="text-xs font-semibold text-muted-foreground">
                        {p.fecha ? p.fecha.split("T")[0] : `Día ${i + 1}`}
                      </p>
                      <div className="my-2">
                        <p className="text-xl font-bold text-foreground">
                          {p.temperatura != null
                            ? `${p.temperatura}°C`
                            : p.temperatura_max != null
                            ? `${p.temperatura_max}°C`
                            : "-"}
                        </p>
                        {p.temperatura_min != null && p.temperatura_max != null && (
                          <p className="text-xs text-muted-foreground">
                            {p.temperatura_min}°C min &bull; {p.temperatura_max}°C max
                          </p>
                        )}
                      </div>
                      <p className="text-xs text-primary truncate">
                        {p.descripcion || "Pronóstico meteorológico"}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
