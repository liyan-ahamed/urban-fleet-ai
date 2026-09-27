"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import AnalyticsPanel from "../components/AnalyticsPanel";
import IncidentsPanel from "../components/IncidentsPanel";
import Sidebar from "../components/Sidebar";

const MapView = dynamic(() => import("../components/MapView"), { ssr: false, loading: () => <div className="flex h-full items-center justify-center rounded-xl border border-neutral-800 bg-[#1a1a1a] text-sm text-neutral-400">Loading map…</div> });

export default function Home() {
  const [active, setActive] = useState("map");
  return <main className="flex h-screen overflow-hidden bg-[#0a0a0a]"><Sidebar active={active} onChange={setActive} /><div className="min-w-0 flex-1 p-5 md:p-8"><header className="mb-7 flex items-center justify-between border-b border-neutral-800 pb-6"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-neutral-400">Operations dashboard <span className="mx-2 text-neutral-600">/</span> Command center</p><h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">{active === "map" ? "Live Map" : active === "incidents" ? "Incidents" : "Analytics"}</h2></div><span className="inline-flex items-center gap-2 rounded-full border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-xs font-semibold text-neutral-300"><span className="h-2 w-2 rounded-full bg-neutral-300" />API live</span></header><div className={active === "map" ? "h-[calc(100%-112px)]" : "h-[calc(100%-112px)] overflow-y-auto pr-1"}>{active === "map" && <MapView />}{active === "incidents" && <IncidentsPanel />}{active === "analytics" && <AnalyticsPanel />}</div></div></main>;
}
