"use client";

import { useEffect, useRef, useState } from "react";

interface WeatherMapProps {
  onLocationSelect: (lat: number, lng: number) => void;
  selectedLat?: number | null;
  selectedLng?: number | null;
}

export function WeatherMap({
  onLocationSelect,
  selectedLat,
  selectedLng,
}: WeatherMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);
  const markerRef = useRef<unknown>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Cargar Leaflet dinamicamente
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = () => {
      const L = (window as unknown as { L: typeof import("leaflet") }).L;

      const map = L.map(mapRef.current!, {
        center: [6.2442, -75.5812], // Medellin / Colombia default
        zoom: 6,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "OpenStreetMap",
      }).addTo(map);

      map.on("click", (e: { latlng: { lat: number; lng: number } }) => {
        const { lat, lng } = e.latlng;
        onLocationSelect(
          Math.round(lat * 10000) / 10000,
          Math.round(lng * 10000) / 10000,
        );
      });

      mapInstanceRef.current = map;
      setReady(true);
    };
    document.head.appendChild(script);

    return () => {
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove();
        mapInstanceRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Actualizar marker
  useEffect(() => {
    if (!ready || !mapInstanceRef.current) return;
    if (selectedLat == null || selectedLng == null) return;

    const L = (window as unknown as { L: typeof import("leaflet") }).L;
    const map = mapInstanceRef.current as import("leaflet").Map;

    if (markerRef.current) {
      (markerRef.current as import("leaflet").Marker).setLatLng([
        selectedLat,
        selectedLng,
      ]);
    } else {
      markerRef.current = L.marker([selectedLat, selectedLng]).addTo(map);
    }

    map.setView([selectedLat, selectedLng], Math.max(map.getZoom(), 8));
  }, [selectedLat, selectedLng, ready]);

  return (
    <div
      ref={mapRef}
      className="h-full w-full rounded-lg"
      style={{ minHeight: 400 }}
    />
  );
}
