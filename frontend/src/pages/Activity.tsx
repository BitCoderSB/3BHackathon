import { useState, useMemo } from "react";
import { MOCK_NARRATIVES, MOCK_EVENTS, MOCK_STORE } from "../mocks/mockData";
import type { NarrativeMessage } from "../types";

type SeverityFilter = "all" | "info" | "warning" | "critical";

export default function Activity() {
  const [severity, setSeverity] = useState<SeverityFilter>("all");
  const [camFilter, setCamFilter] = useState<string | "all">("all");

  const filteredNarratives = useMemo(() => {
    let list = [...MOCK_NARRATIVES];
    if (severity !== "all") list = list.filter(n => n.severity === severity);
    if (camFilter !== "all") list = list.filter(n => n.source_id === camFilter);
    return list.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [severity, camFilter]);

  const filteredEvents = useMemo(() => {
    let list = [...MOCK_EVENTS];
    if (camFilter !== "all") list = list.filter(e => e.source_id === camFilter);
    return list.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [camFilter]);

  const totalEvents = filteredEvents.length;
  const removedCount = filteredEvents.filter(e => e.action === "removed").length;
  const returnedCount = filteredEvents.filter(e => e.action === "returned").length;
  const criticalCount = filteredNarratives.filter(n => n.severity === "critical").length;

  return (
    <div className="p-4 space-y-4">
      {/* ── Header — skill typography ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-heading">Registro de Actividad</h1>
          <p className="text-dense-xs text-gray-400 mt-0.5">Narrativa inteligente y eventos del sistema</p>
        </div>
        <div className="flex gap-1">
          {["all", ...MOCK_STORE.cameras.map(c => c.source_id)].map(id => (
            <button
              key={id}
              onClick={() => setCamFilter(id)}
              className={`pill-toggle ${camFilter === id ? "pill-toggle-active" : "pill-toggle-inactive"}`}
            >
              {id === "all" ? "Todas" : MOCK_STORE.cameras.find(c => c.source_id === id)?.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── KPI Row — skill: kpi-card + slide-in ── */}
      <div className="grid grid-cols-4 gap-grid-gap">
        {[
          { icon: "📊", label: "Total Eventos", value: totalEvents, bg: "bg-status-blue/10" },
          { icon: "↓", label: "Retiros", value: removedCount, bg: "bg-status-red/10", color: "text-status-red" },
          { icon: "↑", label: "Devoluciones", value: returnedCount, bg: "bg-status-green/10", color: "text-status-green" },
          { icon: "🔔", label: "Alertas Críticas", value: criticalCount, bg: "bg-status-red/10", color: criticalCount > 0 ? "text-critical" : "" },
        ].map((kpi, i) => (
          <div key={i} className="kpi-card" style={{ animationDelay: `${i * 50}ms` }}>
            <div className={`kpi-icon ${kpi.bg}`}>{kpi.icon}</div>
            <div>
              <p className={`kpi-value ${kpi.color || ""}`}>{kpi.value}</p>
              <p className="kpi-label">{kpi.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Main Grid: Narrativa + Eventos — skill: 12-col ── */}
      <div className="grid grid-cols-12 gap-grid-gap">
        {/* Narrative Log — 5 cols */}
        <div className="col-span-5 bento-card-static p-card-pad flex flex-col max-h-[520px]">
          <div className="flex items-center justify-between mb-3">
            <h2 className="card-heading">Narrativa del Sistema</h2>
            {/* Severity filter — skill: pill-toggle with severity colors */}
            <div className="flex gap-1">
              {(["all", "info", "warning", "critical"] as const).map(s => {
                const active = severity === s;
                const activeClass =
                  s === "critical" ? "!bg-critical !text-white" :
                  s === "warning" ? "!bg-status-yellow !text-white" :
                  s === "info" ? "!bg-status-blue !text-white" :
                  "";
                return (
                  <button
                    key={s}
                    onClick={() => setSeverity(s)}
                    className={`pill-toggle ${active ? `pill-toggle-active ${activeClass}` : "pill-toggle-inactive"}`}
                  >
                    {s === "all" ? "Todos" : s === "info" ? "Info" : s === "warning" ? "Aviso" : "Crítico"}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {filteredNarratives.length === 0 ? (
              <div className="flex-1 flex items-center justify-center py-12">
                <p className="text-dense-sm text-gray-300">Sin mensajes</p>
              </div>
            ) : (
              filteredNarratives.map((msg, i) => (
                <NarrativeRow key={msg.message_id} message={msg} delay={i * 30} />
              ))
            )}
          </div>
        </div>

        {/* Events Table — 7 cols, skill: data-table, 36px rows, sticky headers */}
        <div className="col-span-7 bento-card-static overflow-hidden flex flex-col max-h-[520px]">
          <div className="px-card-pad pt-3 pb-2 border-b border-gray-100">
            <h2 className="card-heading">Tabla de Eventos</h2>
          </div>
          <div className="flex-1 overflow-y-auto data-table">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="text-left">Hora</th>
                  <th className="text-left">Producto</th>
                  <th className="text-left">Acción</th>
                  <th className="text-left">Stock</th>
                  <th className="text-left">Cam</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map(ev => (
                  <tr key={ev.event_id}>
                    <td className="text-gray-500 font-mono whitespace-nowrap tabular-nums">
                      {new Date(ev.timestamp).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                    </td>
                    <td className="font-medium text-gray-700 truncate max-w-[140px]">{ev.sku_name}</td>
                    <td>
                      <span className={`status-badge ${
                        ev.action === "removed" ? "bg-status-red/10 text-status-red" : "bg-status-green/10 text-status-green"
                      }`}>
                        {ev.action === "removed" ? "↓ Retiro" : "↑ Devol."}
                      </span>
                    </td>
                    <td className="text-gray-600 font-mono tabular-nums">{ev.stock_before}→{ev.stock_after}</td>
                    <td className="text-gray-400">{ev.source_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Narrative Row — skill: alert-bar pattern with severity border ── */
function NarrativeRow({ message, delay }: { message: NarrativeMessage; delay: number }) {
  const borderClass =
    message.severity === "critical" ? "border-l-critical bg-status-red/[0.03]" :
    message.severity === "warning" ? "border-l-status-yellow bg-status-yellow/[0.03]" :
    "border-l-status-blue bg-white";

  return (
    <div
      className={`rounded-xl px-3 py-2 animate-slide-in ${borderClass}`}
      style={{ borderLeftWidth: "3px", borderLeftStyle: "solid", animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start gap-2">
        <span className="text-sm flex-shrink-0 mt-px">{message.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-dense-xs text-gray-700 leading-relaxed">{message.text}</p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="text-[9px] text-gray-400 tabular-nums">
              {new Date(message.timestamp).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })}
            </span>
            <span className="text-[9px] text-gray-200">•</span>
            <span className="text-[9px] text-gray-400">{message.source_id}</span>
            <span className={`status-badge text-[8px] ml-auto ${
              message.severity === "critical" ? "bg-status-red/10 text-status-red" :
              message.severity === "warning" ? "bg-status-yellow/10 text-status-yellow" :
              "bg-status-blue/10 text-status-blue"
            }`}>
              {message.severity}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
