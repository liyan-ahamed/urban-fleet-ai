"use client";

import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { api } from "../lib/api";
import HeatmapLayer from "./HeatmapLayer";

const colors = { pothole: "#f97316", hit_and_run: "#ef4444", rash_driving: "#ef4444", missing_signage: "#eab308", waterlogging: "#3b82f6", vehicle_density: "#22c55e", pedestrian_risk: "#a855f7" };
const label = type => type.replaceAll("_", " ");

export default function MapView() {
  const [events, setEvents] = useState([]); const [heatmap, setHeatmap] = useState(false);
  useEffect(() => { api.get("/events").then(r => setEvents(r.data)).catch(console.error); }, []);
  return <section className="relative h-full overflow-hidden rounded-xl border border-neutral-800 bg-[#1a1a1a] p-2 ">
    <div className="h-full overflow-hidden rounded-lg"><div className="absolute left-6 top-6 z-[500] rounded-lg border border-neutral-800 bg-[#0a0a0a]/95 p-4 shadow-xl backdrop-blur"><p className="text-sm font-semibold text-white">Live Chennai event map</p><p className="mt-1 text-xs text-neutral-400">AI detections across active fleet routes</p><label className="mt-4 flex cursor-pointer items-center justify-between gap-4 text-xs font-medium text-neutral-200">Heatmap overlay<input className="peer sr-only" type="checkbox" checked={heatmap} onChange={e => setHeatmap(e.target.checked)} /><span className="relative h-5 w-9 rounded-full bg-neutral-700 transition peer-checked:bg-neutral-300 peer-focus-visible:ring-2 peer-focus-visible:ring-neutral-400/70 after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition peer-checked:after:translate-x-4" /></label></div>
    <div className="absolute bottom-10 right-6 z-[500] rounded-lg border border-neutral-800 bg-[#0a0a0a]/95 p-3 shadow-xl backdrop-blur"><p className="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-neutral-400">Event legend</p><div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-neutral-200"><Legend color={colors.pothole} label="Pothole" /><Legend color={colors.hit_and_run} label="Incident" /><Legend color={colors.waterlogging} label="Waterlogging" /><Legend color={colors.vehicle_density} label="Traffic density" /><Legend color={colors.pedestrian_risk} label="Pedestrian risk" /></div></div>
    <MapContainer center={[13.0827, 80.2707]} zoom={12} scrollWheelZoom className="h-full"><TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {events.map(event => <CircleMarker key={event.id} center={[event.lat, event.lng]} radius={7} pathOptions={{ color: colors[event.type], fillColor: colors[event.type], fillOpacity: 0.85, weight: 2 }}><Popup><div className="min-w-48 text-neutral-200"><strong className="capitalize text-white">{label(event.type)}</strong><br />Confidence: {(event.confidence * 100).toFixed(0)}%<br />Bus: {event.bus_id}<br />Time: {new Date(event.timestamp).toLocaleString()}<br />{event.plate_number && <>Plate: {event.plate_number}<br /></>}{event.severity && <>Severity: {event.severity}<br /></>}{event.vehicle_count && <>Vehicles: {event.vehicle_count}</>}</div></Popup></CircleMarker>)}
      <HeatmapLayer enabled={heatmap} />
    </MapContainer></div>
  </section>;
}

function Legend({ color, label }) { return <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }} />{label}</span>; }
