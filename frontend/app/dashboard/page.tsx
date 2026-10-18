"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  CalendarDays,
  Key,
  MapPin,
  Thermometer,
  Droplets,
  Gauge,
  Wind,
  Database,
  ArrowUpRight,
  Activity,
  CloudSun,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/stat-card";
import { api } from "@/lib/api-client";
import type { DashboardStats } from "@/lib/types";

// Datos de demo para cuando el backend no responde
const DEMO_STATS: DashboardStats = {
  total_consultas: 284,
  consultas_hoy: 12,
  api_keys_activas: 3,
  ciudades_frecuentes: [
    { ciudad: "Ciudad de Mexico", count: 58 },
    { ciudad: "Guadalajara", count: 42 },
    { ciudad: "Monterrey", count: 37 },
    { ciudad: "Bogota", count: 29 },
    { ciudad: "Lima", count: 24 },
  ],
  consultas_por_dia: [
    { fecha: "Lun", count: 32 },
    { fecha: "Mar", count: 45 },
    { fecha: "Mie", count: 28 },
    { fecha: "Jue", count: 56 },
    { fecha: "Vie", count: 41 },
    { fecha: "Sab", count: 38 },
    { fecha: "Dom", count: 44 },
  ],
  promedios: {
    temperatura: 22.5,
    humedad: 65,
    presion: 1013.2,
    viento: 12.4,
  },
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>(DEMO_STATS);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    api
      .get<DashboardStats>("/dashboard/stats")
      .then(setStats)
      .catch(() => {
        // Backend no disponible, usar datos demo
        setStats(DEMO_STATS);
      })
      .finally(() => setLoadingStats(false));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-border/60 bg-gradient-to-r from-card via-card to-primary/5 p-6 shadow-sm">
        <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-500">
                Sistema Operativo &bull; MariaDB / MySQL Activo
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Panel Meteorológico ClimaGuru
            </h1>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Consulta datos meteorológicos en tiempo real, análisis histórico y estado de bases de datos.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              href="/dashboard/mapa"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-md transition-all hover:bg-primary/90 hover:shadow-primary/25"
            >
              <CloudSun className="h-4 w-4" />
              <span>Consultar Mapa</span>
            </Link>
            <a
              href="http://localhost:8080"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-border/80 bg-background/80 px-4 py-2.5 text-sm font-semibold text-foreground backdrop-blur-sm transition-all hover:bg-secondary"
            >
              <Database className="h-4 w-4 text-emerald-500" />
              <span>phpMyAdmin</span>
              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
            </a>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Consultas"
          value={stats.total_consultas}
          icon={BarChart3}
          subtitle="Todas las consultas"
        />
        <StatCard
          title="Consultas Hoy"
          value={stats.consultas_hoy}
          icon={CalendarDays}
          subtitle="Ultimas 24 horas"
        />
        <StatCard
          title="API Keys Activas"
          value={stats.api_keys_activas}
          icon={Key}
          subtitle="Proveedores configurados"
        />
        <StatCard
          title="Ciudades Consultadas"
          value={stats.ciudades_frecuentes.length}
          icon={MapPin}
          subtitle="Ubicaciones unicas"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Activity chart */}
        <Card className="border-border/50 lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-card-foreground">
              Actividad Semanal
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.consultas_por_dia}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(213,94%,54%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(213,94%,54%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,18%,18%)" />
                  <XAxis
                    dataKey="fecha"
                    tick={{ fill: "hsl(215,14%,55%)", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "hsl(215,14%,55%)", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(222,25%,11%)",
                      border: "1px solid hsl(220,18%,18%)",
                      borderRadius: "8px",
                      color: "hsl(210,20%,95%)",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="hsl(213,94%,54%)"
                    strokeWidth={2}
                    fill="url(#colorCount)"
                    name="Consultas"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top cities */}
        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-card-foreground">
              Ciudades Frecuentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={stats.ciudades_frecuentes}
                  layout="vertical"
                  margin={{ left: 0, right: 16 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="hsl(220,18%,18%)"
                    horizontal={false}
                  />
                  <XAxis
                    type="number"
                    tick={{ fill: "hsl(215,14%,55%)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    dataKey="ciudad"
                    type="category"
                    tick={{ fill: "hsl(215,14%,55%)", fontSize: 11 }}
                    width={110}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(222,25%,11%)",
                      border: "1px solid hsl(220,18%,18%)",
                      borderRadius: "8px",
                      color: "hsl(210,20%,95%)",
                    }}
                  />
                  <Bar
                    dataKey="count"
                    fill="hsl(190,80%,50%)"
                    radius={[0, 4, 4, 0]}
                    name="Consultas"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Weather averages */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border/50">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-chart-3/15">
              <Thermometer className="h-5 w-5" style={{ color: "hsl(30,90%,60%)" }} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Temp. Promedio</p>
              <p className="text-xl font-bold text-card-foreground">
                {stats.promedios.temperatura}°C
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Droplets className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Humedad Promedio</p>
              <p className="text-xl font-bold text-card-foreground">
                {stats.promedios.humedad}%
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-chart-4/15">
              <Gauge className="h-5 w-5" style={{ color: "hsl(150,60%,48%)" }} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Presion Promedio</p>
              <p className="text-xl font-bold text-card-foreground">
                {stats.promedios.presion} hPa
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-accent/10">
              <Wind className="h-5 w-5 text-accent" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Viento Promedio</p>
              <p className="text-xl font-bold text-card-foreground">
                {stats.promedios.viento} km/h
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
