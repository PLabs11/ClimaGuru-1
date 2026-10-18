"use client";

import React, { useEffect, useState } from "react";
import {
  Key,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  ShieldCheck,
  ShieldOff,
  CloudSun,
  Sparkles,
  ExternalLink,
  Layers,
  Database,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import type { ApiKey } from "@/lib/types";

const PROVIDERS = [
  {
    value: "meteoblue",
    label: "Meteoblue (Modelos NMM y Pronóstico por Paquetes)",
    desc: "API suiza de alta resolución meteorológica",
    url: "https://my.meteoblue.com",
    badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  },
  {
    value: "meteosource",
    label: "Meteosource (AI & Machine Learning Weather)",
    desc: "Predicción meteorológica con inteligencia artificial",
    url: "https://www.meteosource.com",
    badgeClass: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  },
  {
    value: "openweathermap",
    label: "OpenWeatherMap (Condiciones Globales)",
    desc: "Datos en tiempo real y pronósticos estándar",
    url: "https://openweathermap.org",
    badgeClass: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  },
  {
    value: "weatherapi",
    label: "WeatherAPI",
    desc: "API multipropósito de pronóstico y alertas",
    url: "https://weatherapi.com",
    badgeClass: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  },
  {
    value: "visualcrossing",
    label: "Visual Crossing",
    desc: "Datos históricos y pronóstico",
    url: "https://visualcrossing.com",
    badgeClass: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  },
  {
    value: "otro",
    label: "Otro proveedor",
    desc: "Servicio personalizado",
    url: "",
    badgeClass: "bg-secondary text-secondary-foreground",
  },
];

// Datos por defecto si el backend no responde
const DEMO_KEYS: ApiKey[] = [
  {
    id: 1,
    usuario_id: 1,
    proveedor: "meteoblue",
    api_key: "0dvO2kqZSoiAmb7g",
    activa: true,
    creada_en: "2026-02-01T10:00:00",
  },
  {
    id: 2,
    usuario_id: 1,
    proveedor: "meteosource",
    api_key: "yhverrxl1iqgzypamd6rtv30uhxwlych29g1depb",
    activa: true,
    creada_en: "2026-02-01T10:30:00",
  },
  {
    id: 3,
    usuario_id: 1,
    proveedor: "openweathermap",
    api_key: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    activa: true,
    creada_en: "2026-01-15T10:30:00",
  },
];

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>(DEMO_KEYS);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [proveedor, setProveedor] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    api
      .get<{ api_keys: ApiKey[] }>("/api-keys")
      .then((res) => {
        if (res.api_keys && res.api_keys.length > 0) {
          setKeys(res.api_keys);
        } else {
          setKeys(DEMO_KEYS);
        }
      })
      .catch(() => setKeys(DEMO_KEYS))
      .finally(() => setLoading(false));
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setSaving(true);
    try {
      const res = await api.post<{ api_key: ApiKey; message?: string }>("/api-keys", {
        proveedor,
        api_key: apiKey,
      });
      const newKey = res.api_key || (res as unknown as ApiKey);
      setKeys((prev) => [...prev.filter((k) => k.proveedor !== proveedor), newKey]);
      setShowForm(false);
      setProveedor("");
      setApiKey("");
      setSuccessMsg("API Key guardada exitosamente en la base de datos.");
      setTimeout(() => setSuccessMsg(""), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar la API Key");
    } finally {
      setSaving(false);
    }
  }

  async function handleToggle(id: number, activa: boolean) {
    try {
      await api.put(`/api-keys/${id}`, { activa: !activa });
      setKeys((prev) =>
        prev.map((k) => (k.id === id ? { ...k, activa: !activa } : k))
      );
    } catch {
      // Toggle local para demo si la API falla
      setKeys((prev) =>
        prev.map((k) => (k.id === id ? { ...k, activa: !activa } : k))
      );
    }
  }

  async function handleDelete(id: number) {
    try {
      await api.delete(`/api-keys/${id}`);
      setKeys((prev) => prev.filter((k) => k.id !== id));
    } catch {
      setKeys((prev) => prev.filter((k) => k.id !== id));
    }
  }

  function toggleVisibility(id: number) {
    setVisibleKeys((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function maskKey(key: string) {
    if (!key) return "********";
    if (key.length <= 8) return "********";
    return key.slice(0, 4) + "••••••••" + key.slice(-4);
  }

  function getProviderMeta(prov: string) {
    const p = PROVIDERS.find((item) => item.value === prov.toLowerCase());
    return (
      p || {
        value: prov,
        label: prov.toUpperCase(),
        desc: "Proveedor meteorológico",
        url: "",
        badgeClass: "bg-secondary text-secondary-foreground",
      }
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5" /> Claves Encriptadas en MySQL
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Gestión de API Keys Meteorológicas
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Administra tus credenciales de <strong className="text-foreground">Meteoblue</strong>,{" "}
            <strong className="text-foreground">Meteosource</strong>, OpenWeatherMap y otros proveedores.
          </p>
        </div>

        <Button onClick={() => setShowForm(!showForm)} className="shadow-md">
          <Plus className="mr-2 h-4 w-4" />
          {showForm ? "Cerrar Formulario" : "Nueva API Key"}
        </Button>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-400">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Overview Cards for Meteoblue & Meteosource */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Meteoblue Info Card */}
        <Card className="border-blue-500/30 bg-gradient-to-br from-card to-blue-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/15 text-blue-400">
                  <CloudSun className="h-4 w-4" />
                </span>
                <CardTitle className="text-base font-bold text-card-foreground">
                  Meteoblue
                </CardTitle>
              </div>
              <Badge variant="outline" className="text-[10px] text-blue-400 border-blue-500/30">
                Modelos NMM
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground flex flex-col justify-between gap-3">
            <p>
              Simulaciones atmosféricas suizas de alta resolución (NMM), pronósticos de 7 días y variables de viento por capas.
            </p>
            <div className="flex items-center justify-between pt-1 border-t border-border/40">
              <span className="text-[11px] font-medium text-blue-400">Endpoint: /packages/basic-day</span>
              <a
                href="https://my.meteoblue.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-primary hover:underline text-[11px]"
              >
                <span>Portal API</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Meteosource Info Card */}
        <Card className="border-emerald-500/30 bg-gradient-to-br from-card to-emerald-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400">
                  <Sparkles className="h-4 w-4" />
                </span>
                <CardTitle className="text-base font-bold text-card-foreground">
                  Meteosource
                </CardTitle>
              </div>
              <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-500/30">
                Machine Learning
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground flex flex-col justify-between gap-3">
            <p>
              Previsiones meteorológicas optimizadas mediante algoritmos de inteligencia artificial y modelos globales agregados.
            </p>
            <div className="flex items-center justify-between pt-1 border-t border-border/40">
              <span className="text-[11px] font-medium text-emerald-400">Endpoint: /v1/free/point</span>
              <a
                href="https://www.meteosource.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-primary hover:underline text-[11px]"
              >
                <span>Portal API</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        {/* IDEAM & Open-Meteo Info Card */}
        <Card className="border-amber-500/30 bg-gradient-to-br from-card to-amber-500/5 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/15 text-base">
                  🇨🇴
                </span>
                <CardTitle className="text-base font-bold text-card-foreground">
                  IDEAM & Open-Meteo
                </CardTitle>
              </div>
              <Badge variant="outline" className="text-[10px] text-amber-400 border-amber-500/30">
                Sin API Key
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground flex flex-col justify-between gap-3">
            <p>
              Estaciones meteorológicas oficiales de Colombia (datos.gov.co) y reanálisis ERA5 de alta precisión integrados de forma nativa.
            </p>
            <div className="flex items-center justify-between pt-1 border-t border-border/40">
              <span className="text-[11px] font-medium text-amber-400">Red Nacional &bull; Gratuito</span>
              <a
                href="https://www.datos.gov.co/d/sbwg-7ju4"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-primary hover:underline text-[11px]"
              >
                <span>datos.gov.co</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add form */}
      {showForm && (
        <Card className="border-border/60 shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-card-foreground flex items-center gap-2">
              <Key className="h-4 w-4 text-primary" />
              Configurar Nueva API Key
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAdd} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="flex flex-col gap-2">
                  <Label>Proveedor Meteorológico</Label>
                  <Select value={proveedor} onValueChange={setProveedor}>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar proveedor..." />
                    </SelectTrigger>
                    <SelectContent>
                      {PROVIDERS.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex flex-col gap-2 sm:col-span-2">
                  <Label>Clave de API (Secret / Token)</Label>
                  <Input
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Pega tu clave de API aquí..."
                    required
                    className="font-mono text-xs"
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 rounded-lg bg-destructive/15 border border-destructive/30 p-3 text-xs text-destructive">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-1">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForm(false)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={saving || !proveedor || !apiKey}>
                  {saving ? "Guardando en BD..." : "Guardar API Key"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Keys list */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Layers className="h-4 w-4" /> Proveedores y Claves Configuradas
          </h2>
          <span className="text-xs text-muted-foreground">
            {keys.length} clave(s) registrada(s)
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : keys.length === 0 ? (
          <Card className="border-border/50">
            <CardContent className="flex flex-col items-center gap-3 py-12">
              <Key className="h-10 w-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No tienes API keys configuradas
              </p>
              <Button variant="outline" onClick={() => setShowForm(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Agregar primera key
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="flex flex-col gap-3">
            {keys.map((k) => {
              const meta = getProviderMeta(k.proveedor);
              const isVisible = visibleKeys.has(k.id);
              const keyVal = k.api_key || "";

              return (
                <Card
                  key={k.id}
                  className="border-border/60 shadow-sm transition-all hover:border-border"
                >
                  <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-3.5">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary">
                        <Key className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-bold text-card-foreground capitalize">
                            {meta.label}
                          </p>
                          <Badge
                            variant="secondary"
                            className={`text-xs ${meta.badgeClass}`}
                          >
                            {k.proveedor}
                          </Badge>
                          <Badge
                            variant={k.activa ? "default" : "secondary"}
                            className="text-[10px]"
                          >
                            {k.activa ? "Activa" : "Inactiva"}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="font-mono text-xs text-muted-foreground">
                            {isVisible ? keyVal : maskKey(keyVal)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 self-end sm:self-center">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleVisibility(k.id)}
                        title={isVisible ? "Ocultar key" : "Mostrar key"}
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                      >
                        {isVisible ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleToggle(k.id, k.activa)}
                        title={k.activa ? "Desactivar proveedor" : "Activar proveedor"}
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                      >
                        {k.activa ? (
                          <ShieldCheck className="h-4 w-4 text-emerald-400" />
                        ) : (
                          <ShieldOff className="h-4 w-4 text-muted-foreground" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(k.id)}
                        title="Eliminar key"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
