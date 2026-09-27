"use client";

import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import { api } from "../lib/api";

export default function HeatmapLayer({ enabled }) {
  const map = useMap();
  useEffect(() => {
    let layer;
    if (enabled) api.get("/analytics/heatmap").then(({ data }) => {
      layer = L.heatLayer(data.map(p => [p.lat, p.lng, p.weight]), { radius: 27, blur: 22, maxZoom: 15, gradient: { 0.2: "#22c55e", 0.5: "#eab308", 0.8: "#f97316", 1: "#ef4444" } }).addTo(map);
    }).catch(console.error);
    return () => { if (layer) map.removeLayer(layer); };
  }, [enabled, map]);
  return null;
}
