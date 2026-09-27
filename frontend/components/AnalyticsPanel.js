"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";

const pretty = value => value.replaceAll("_", " ");

export default function AnalyticsPanel() {
  const [summary, setSummary] = useState([]); const [timeline, setTimeline] = useState([]);
  useEffect(() => { api.get("/analytics/summary").then(({ data }) => setSummary(data.map(d => ({ ...d, type: pretty(d.type) })))).catch(console.error); api.get("/events").then(({ data }) => { const buckets = {}; data.filter(e => new Date(e.timestamp) >= new Date(Date.now() - 72 * 3600000)).forEach(e => { const hour = new Date(e.timestamp).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit" }); buckets[hour] = (buckets[hour] || 0) + 1; }); setTimeline(Object.entries(buckets).map(([hour, count]) => ({ hour, count }))); }).catch(console.error); }, []);
  return <section><div className="mb-7 border-b border-neutral-800 pb-6"><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-neutral-400">Network intelligence</p><h2 className="mt-2 text-2xl font-bold tracking-tight text-white">Fleet analytics</h2><p className="mt-1 text-sm text-neutral-400">Event distribution and recent detection volume</p></div><div className="grid gap-6 xl:grid-cols-2"><ChartCard title="Events by type"><ResponsiveContainer width="100%" height={310}><BarChart data={summary}><CartesianGrid strokeDasharray="3 3" stroke="#404040" /><XAxis dataKey="type" tick={{ fill: "#a3a3a3", fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={75} /><YAxis tick={{ fill: "#a3a3a3" }} /><Tooltip contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #404040", borderRadius: 8 }} /><Bar dataKey="count" fill="#a3a3a3" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></ChartCard><ChartCard title="Events over the last 72 hours"><ResponsiveContainer width="100%" height={310}><LineChart data={timeline}><CartesianGrid strokeDasharray="3 3" stroke="#404040" /><XAxis dataKey="hour" tick={{ fill: "#a3a3a3", fontSize: 10 }} interval="preserveStartEnd" /><YAxis tick={{ fill: "#a3a3a3" }} /><Tooltip contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #404040", borderRadius: 8 }} /><Legend /><Line type="monotone" dataKey="count" name="Events" stroke="#737373" strokeWidth={3} dot={false} /></LineChart></ResponsiveContainer></ChartCard></div></section>;
}

function ChartCard({ title, children }) { return <div className="rounded-xl border border-neutral-800 bg-[#1a1a1a] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.22)]"><h3 className="mb-5 text-base font-semibold text-white">{title}</h3>{children}</div>; }
