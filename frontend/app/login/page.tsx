"use client";

import React from "react"

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Cloud, Eye, EyeOff, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ username, password });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesion");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4 overflow-hidden">
      {/* Dynamic ambient background glows */}
      <div className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full bg-primary/15 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-accent/15 blur-3xl" />
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-chart-3/5 blur-[120px]" />

      <div className="relative z-10 flex w-full max-w-md flex-col items-center gap-6">
        {/* Logo and title with glow */}
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary via-primary/90 to-accent shadow-lg shadow-primary/25">
              <Cloud className="h-8 w-8 text-primary-foreground animate-pulse" />
            </div>
            <span className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-foreground via-foreground to-foreground/70 bg-clip-text">
              ClimaGuru
            </span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-border/80 bg-secondary/50 px-3 py-1 text-xs text-muted-foreground backdrop-blur-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
            <span>Sistema Conectado a MariaDB / MySQL</span>
          </div>
        </div>

        <Card className="w-full border-border/60 bg-card/80 backdrop-blur-xl shadow-2xl transition-all">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl font-bold tracking-tight text-card-foreground">
              Bienvenido de nuevo
            </CardTitle>
            <CardDescription className="text-sm">
              Accede a la plataforma de monitoreo y análisis meteorológico
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Quick Login Presets */}
            <div className="rounded-xl border border-border/50 bg-secondary/30 p-3">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                Credenciales de acceso rápido (MySQL):
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setUsername("admin");
                    setPassword("admin123");
                  }}
                  className="flex flex-col items-start rounded-lg border border-primary/20 bg-primary/5 p-2 text-left transition hover:bg-primary/10 hover:border-primary/40"
                >
                  <span className="text-xs font-semibold text-primary">👑 Administrador</span>
                  <span className="text-[10px] text-muted-foreground">admin / admin123</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setUsername("operario1");
                    setPassword("admin123");
                  }}
                  className="flex flex-col items-start rounded-lg border border-accent/20 bg-accent/5 p-2 text-left transition hover:bg-accent/10 hover:border-accent/40"
                >
                  <span className="text-xs font-semibold text-accent">🔧 Operario Demo</span>
                  <span className="text-[10px] text-muted-foreground">operario1 / admin123</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-center gap-2">
                  <span>⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="username" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Usuario o Correo
                </Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  required
                  autoComplete="username"
                  className="h-11 bg-background/50 border-border/80 focus-visible:ring-primary"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Contraseña
                  </Label>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    autoComplete="current-password"
                    className="h-11 pr-10 bg-background/50 border-border/80 focus-visible:ring-primary"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    aria-label={showPw ? "Ocultar contraseña" : "Mostrar contraseña"}
                  >
                    {showPw ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button type="submit" className="w-full h-11 font-medium shadow-md transition-all active:scale-[0.98]" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                    Iniciando Sesión...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <LogIn className="h-4 w-4" />
                    Entrar al Dashboard
                  </span>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-sm text-muted-foreground">
          {"¿No tienes cuenta todavía? "}
          <Link
            href="/register"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Regístrate aquí
          </Link>
        </p>
      </div>
    </div>
  );
}
