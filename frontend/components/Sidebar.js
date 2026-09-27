"use client";

const links = [
  ["map", "Live Map", "⌖"],
  ["incidents", "Incidents", "⚠"],
  ["analytics", "Analytics", "▥"],
];

export default function Sidebar({ active, onChange }) {
  return <aside className="flex w-64 flex-col border-r border-neutral-800 bg-[#0a0a0a] px-4 py-7 ">
    <div className="mb-9 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-4"><p className="text-[10px] font-bold uppercase tracking-[0.22em] text-neutral-400">Urban intelligence</p><h1 className="mt-2 text-xl font-bold tracking-tight text-white">Fleet AI</h1><p className="mt-1 text-xs text-neutral-400">Chennai operations</p></div>
    <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-neutral-500">Workspace</p><nav className="space-y-2">{links.map(([id, label, icon]) => <button key={id} onClick={() => onChange(id)} className={`group flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left text-sm font-medium transition-all duration-150 ${active === id ? "border border-transparent bg-neutral-800 text-white shadow-[inset_3px_0_0_#ffffff]" : "border border-transparent text-neutral-400 hover:bg-neutral-800 hover:text-white"}`}><span className={`flex h-7 w-7 items-center justify-center rounded-md text-base ${active === id ? "bg-neutral-700 text-white" : "bg-neutral-900 text-neutral-400 group-hover:text-white"}`}>{icon}</span>{label}</button>)}</nav>
    <div className="mt-auto rounded-xl border border-neutral-800 bg-neutral-900 p-3"><p className="text-xs font-medium text-neutral-300">Detection feed</p><p className="mt-1 text-xs text-neutral-500">Mock data · Prototype v0.1</p></div>
  </aside>;
}
