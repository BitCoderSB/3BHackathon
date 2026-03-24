import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useSocketContext } from "../hooks/useSocket";
import VideoFeed from "../components/VideoFeed";
import type { ProductStock } from "../types";

/* ── SemiCircleGauge (copied from ProductCatalog) ── */
function SemiCircleGauge({
  current, initial,
  ticks: totalTicks = 18,
  strokeW = 2.8,
  gap = 0.02,
  rInner = 18,
  rOuter = 34,
}: {
  current: number; initial: number;
  ticks?: number; strokeW?: number; gap?: number;
  rInner?: number; rOuter?: number;
}) {
  const pct = Math.round((current / initial) * 100);
  const filledTicks = Math.round((pct / 100) * totalTicks);
  const color = pct <= 25 ? "#EF4444" : pct <= 50 ? "#F59E0B" : "#22C55E";

  const cx = 44, cy = 40;
  const totalGap = gap * (totalTicks - 1);
  const availableAngle = Math.PI - totalGap;
  const tickAngle = availableAngle / (totalTicks - 1);

  const tickLines = Array.from({ length: totalTicks }, (_, i) => {
    const angle = Math.PI - i * (tickAngle + gap);
    return (
      <line
        key={i}
        x1={cx + rInner * Math.cos(angle)}
        y1={cy - rInner * Math.sin(angle)}
        x2={cx + rOuter * Math.cos(angle)}
        y2={cy - rOuter * Math.sin(angle)}
        stroke={i < filledTicks ? color : "#E5E7EB"}
        strokeWidth={strokeW}
        strokeLinecap="round"
      />
    );
  });

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 88 44" className="w-20 h-11">
        {tickLines}
      </svg>
      <span className="text-[10px] font-bold tabular-nums -mt-1.5" style={{ color }}>
        {pct}%
      </span>
    </div>
  );
}

/* ── Stock Bar: skill Gauge → Red→Yellow→Green gradient, ALWAYS show value + % ── */
function StockBar({ product }: { product: ProductStock }) {
  const pct = (product.stock_current / product.stock_initial) * 100;
  const barColor =
    pct <= 25 ? "bg-status-red" :
    pct <= 50 ? "bg-status-yellow" :
    "bg-status-green";

  return (
    <div className="flex items-center gap-3" style={{ height: '36px' }}>
      <div className="w-24 text-dense-xs font-medium text-gray-700 truncate" title={product.sku_name}>
        {product.sku_name.split(" ").slice(0, 2).join(" ")}
      </div>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-dense-xs font-bold text-gray-700 w-12 text-right tabular-nums">
        {product.stock_current}/{product.stock_initial}
      </span>
      <span className="text-[10px] font-medium text-gray-400 w-9 text-right tabular-nums">{Math.round(pct)}%</span>
      {product.alert_active && (
        <span className="connection-dot connection-dot-online bg-status-red flex-shrink-0" />
      )}
    </div>
  );
}

export default function LivePanel() {
  const navigate = useNavigate();
  const { products: socketProducts, narratives, events, predictions, connected, usingMock, videoFrame, cameras } = useSocketContext();
  const [selectedCam, setSelectedCam] = useState<string | "all">("all");
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  const products = socketProducts;

  const alerts = narratives.filter(n => n.severity === "critical" || n.severity === "warning");
  const totalProducts = products.length;
  const alertCount = products.filter(p => p.alert_active).length;
  const totalStock = products.reduce((s, p) => s + p.stock_current, 0);
  const maxStock = products.reduce((s, p) => s + p.stock_initial, 0);
  const pctAvail = Math.round((totalStock / maxStock) * 100);

  return (
    <div className="space-y-0">
      {/* ── Top section — white full-width card ── */}
      <div className="bg-white w-full px-6 py-4">
        {/* Header + Connection + Camera toggle */}
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="page-heading flex-shrink-0" style={{ fontSize: '30px' }}>Panel en Vivo</h1>
          <div className="flex items-center gap-3 flex-1 justify-end">
            <div className="flex items-center gap-1.5 text-gray-400">
              <span className={`connection-dot ${connected ? "connection-dot-online" : "connection-dot-offline"}`} />
              <span className="text-[10px] font-medium">{connected ? "Conectado" : usingMock ? "Mock" : "Desconectado"}</span>
            </div>
            <div className="h-5 w-px bg-gray-200" />
            <div className="flex gap-1">
              {["all" as const, ...cameras.map(c => c.source_id)].map(id => (
                <button
                  key={id}
                  onClick={() => setSelectedCam(id)}
                  className={`pill-toggle ${selectedCam === id ? "pill-toggle-active" : "pill-toggle-inactive"}`}
                >
                  {id === "all" ? "Todas" : cameras.find(c => c.source_id === id)?.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Alert Banner — one at a time, dismissible, click → Activity */}
        {(() => {
          const visibleAlert = alerts.find(a => !dismissedAlerts.has(a.message_id));
          if (!visibleAlert) return null;
          return (
            <div
              className="mt-3 flex items-center gap-3 px-4 py-2.5 rounded-lg border-l-4 border-red-500 bg-red-50 cursor-pointer transition-colors hover:bg-red-100"
              onClick={() => navigate('/activity')}
            >
              <span className="text-base flex-shrink-0">{visibleAlert.icon}</span>
              <span className="flex-1 text-[13px] font-medium text-gray-700 truncate">{visibleAlert.text}</span>
              <span className="text-[10px] text-gray-400 flex-shrink-0">{alerts.filter(a => !dismissedAlerts.has(a.message_id)).length} alerta{alerts.filter(a => !dismissedAlerts.has(a.message_id)).length !== 1 ? 's' : ''}</span>
              <button
                onClick={(e) => { e.stopPropagation(); setDismissedAlerts(prev => new Set(prev).add(visibleAlert.message_id)); }}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none flex-shrink-0 px-1"
              >
                ×
              </button>
            </div>
          );
        })()}

        {/* KPI Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-center mt-6 pt-5 border-t border-gray-100 gap-4 sm:gap-8">
          {/* Productos */}
          <div className="flex flex-col items-center">
            <span className="text-[13px] text-[#8A8A8A]">Productos</span>
            <span className="text-[26px] font-semibold text-[#1A1A1A] leading-tight tabular-nums">{totalProducts}</span>
          </div>

          <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
          <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

          {/* Disponibilidad — with SemiCircleGauge */}
          <div className="flex flex-col items-center">
            <span className="text-[13px] text-[#8A8A8A]">Disponibilidad</span>
            <div className="flex items-center gap-2 mt-0.5">
              <SemiCircleGauge current={pctAvail} initial={100} />
              <span className={`text-[14px] font-bold leading-tight ${
                pctAvail <= 25 ? 'text-red-500' : pctAvail <= 50 ? 'text-yellow-500' : 'text-green-500'
              }`}>
                {pctAvail <= 25 ? 'Crítico' : pctAvail <= 50 ? 'Bajo' : 'Bueno'}
              </span>
            </div>
          </div>

          <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
          <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

          {/* Alertas Activas */}
          <div className="flex flex-col items-center">
            <span className="text-[13px] text-[#8A8A8A]">Alertas Activas</span>
            <span className={`text-[26px] font-semibold leading-tight tabular-nums ${
              alertCount > 0 ? 'text-red-500' : 'text-[#1A1A1A]'
            }`}>{alertCount}</span>
          </div>

          <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
          <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

          {/* Cámaras Online */}
          <div className="flex flex-col items-center">
            <span className="text-[13px] text-[#8A8A8A]">Cámaras Online</span>
            <span className="text-[26px] font-semibold text-[#1A1A1A] leading-tight tabular-nums">{cameras.filter(c => c.status === "online").length}/{cameras.length}</span>
          </div>
        </div>

        {/* Resumen en texto natural */}
        <p className="mt-4 text-[12px] text-gray-500 leading-relaxed text-center max-w-3xl mx-auto">
          {(() => {
            const critical = products.filter(p => p.alert_level === "critical");
            const low = products.filter(p => p.alert_level === "low");
            const topPred = predictions.filter(p => p.minutes_remaining !== null && p.minutes_remaining < 60);
            const okCount = products.filter(p => p.alert_level === "normal").length;
            const parts: string[] = [];

            if (critical.length > 0) {
              parts.push(`${critical.map(p => p.sku_name.split(" ").slice(0, 3).join(" ")).join(" y ")} en nivel crítico`);
            }
            if (topPred.length > 0) {
              parts.push(`${topPred.map(p => p.sku_name.split(" ").slice(0, 3).join(" ")).join(" y ")} podría${topPred.length === 1 ? "" : "n"} agotarse en menos de una hora`);
            }
            if (low.length > 0) {
              parts.push(`${low.map(p => p.sku_name.split(" ").slice(0, 3).join(" ")).join(" y ")} con stock bajo`);
            }

            let summary = okCount === products.length
              ? `Todos los productos están en buen nivel.`
              : `${parts.join(" · ")}. ${okCount} de ${products.length} productos en buen nivel.`;

            summary += " Monitoreado en tiempo real por visión por computadora, sin etiquetas ni sensores.";

            const segments = summary.split(" · ");
            return segments.map((seg, i) => (
              <span key={i}>
                {i > 0 && <span className="text-brand-red font-bold mx-1">·</span>}
                {seg}
              </span>
            ));
          })()}
        </p>
      </div>

      {/* ── Bottom section — full-width background ── */}
      <div className="w-full px-6 py-4" style={{ backgroundColor: 'rgba(249, 249, 249, 1)' }}>
        {/* ── Main Grid ── */}
        <div className="grid grid-cols-12 gap-4">
        {/* Camera Feeds — 8 cols */}
        <div className="col-span-8 space-y-4">
          {selectedCam === "all" ? (
            <div className="grid grid-cols-2 gap-grid-gap">
              {cameras.map(cam => (
                <VideoFeed
                  key={cam.source_id}
                  frame={videoFrame}
                  label={cam.label}
                  location={cam.location}
                />
              ))}
            </div>
          ) : (
            <VideoFeed
              frame={videoFrame}
              label={cameras.find(c => c.source_id === selectedCam)!.label}
              location={cameras.find(c => c.source_id === selectedCam)!.location}
              large
            />
          )}
        </div>

        {/* Stock Panel — 4 cols, horizontal bar chart */}
        <div className="col-span-4 bento-card-static p-card-pad flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h2 className="card-heading">Inventario</h2>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg ${
              pctAvail > 70 ? "bg-status-green/10 text-status-green" :
              pctAvail > 40 ? "bg-status-yellow/10 text-status-yellow" :
              "bg-status-red/10 text-status-red"
            }`}>
              {pctAvail}% disponible
            </span>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ResponsiveContainer width="100%" height={products.length * 42 + 20}>
              <BarChart
                data={products.map(p => ({
                  name: p.sku_name.split(" ").slice(0, 2).join(" "),
                  stock: p.stock_current,
                  initial: p.stock_initial,
                  pct: Math.round((p.stock_current / p.stock_initial) * 100),
                  alert: p.alert_active,
                }))}
                layout="vertical"
                margin={{ top: 4, right: 40, bottom: 4, left: 4 }}
                barCategoryGap="20%"
              >
                <XAxis type="number" domain={[0, 8]} tick={{ fontSize: 10, fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={90}
                  tick={{ fontSize: 11, fill: "#374151" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 12, border: "1px solid #E5E7EB", boxShadow: "0 4px 6px rgba(0,0,0,0.05)" }}
                  formatter={(value: number, _name: string, props: any) => [
                    `${value}/${props.payload.initial} (${props.payload.pct}%)`,
                    "Stock"
                  ]}
                />
                <Bar dataKey="stock" radius={[0, 6, 6, 0]} barSize={16}
                  label={{ position: "right", fontSize: 10, fill: "#6B7280", formatter: (v: number) => `${v}` }}
                >
                  {products.map((p, i) => {
                    const pct = (p.stock_current / p.stock_initial) * 100;
                    const fill = pct <= 25 ? "#EF4444" : pct <= 50 ? "#F59E0B" : "#22C55E";
                    return <Cell key={i} fill={fill} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

        {/* ── Second row — Events + Narrative + Productos en Riesgo ── */}
        <div className="grid grid-cols-12 gap-4 mt-4">
          {/* Últimos Eventos — 5 cols */}
          <div className="col-span-5 bento-card-static overflow-hidden">
            <div className="px-card-pad pt-3 pb-2 border-b border-gray-100 flex items-center justify-between">
              <h2 className="card-heading">Últimos Eventos</h2>
              <span className="text-[10px] text-gray-400">{events.length} eventos</span>
            </div>
            <div className="divide-y divide-gray-50">
              {events.slice(0, 5).map((ev, i) => (
                <div key={ev.event_id} className="px-card-pad py-2 flex items-center gap-3 animate-slide-in" style={{ animationDelay: `${i * 60}ms` }}>
                  <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs flex-shrink-0 ${
                    ev.action === "removed" ? "bg-red-50 text-red-500" : "bg-green-50 text-green-500"
                  }`}>
                    {ev.action === "removed" ? "↓" : "↑"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-dense-xs font-medium text-gray-700 truncate">{ev.sku_name}</p>
                    <p className="text-[10px] text-gray-400">
                      {ev.action === "removed" ? "Retirado" : "Devuelto"} · {ev.stock_before} → {ev.stock_after} uds
                    </p>
                  </div>
                  <span className="text-[10px] text-gray-400 tabular-nums flex-shrink-0">
                    {new Date(ev.timestamp).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Narrativa en Vivo — 4 cols */}
          <div className="col-span-4 bento-card-static overflow-hidden">
            <div className="px-card-pad pt-3 pb-2 border-b border-gray-100 flex items-center justify-between">
              <h2 className="card-heading">Narrativa en Vivo</h2>
              <div className="live-badge" style={{ fontSize: '9px', padding: '1px 6px' }}>
                <span className="w-1 h-1 rounded-full bg-white animate-pulse-live" />
                VIVO
              </div>
            </div>
            <div className="divide-y divide-gray-50 max-h-[260px] overflow-y-auto">
              {narratives.slice().reverse().map((msg, i) => (
                <div key={msg.message_id} className="px-card-pad py-2.5 flex items-start gap-2.5 animate-slide-in" style={{ animationDelay: `${i * 60}ms` }}>
                  <span className="text-sm flex-shrink-0 mt-0.5">{msg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-dense-xs text-gray-700 leading-snug">{msg.text}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[9px] text-gray-400 tabular-nums">
                        {new Date(msg.timestamp).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                      </span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-medium ${
                        msg.severity === "critical" ? "bg-red-50 text-red-500" :
                        msg.severity === "warning" ? "bg-amber-50 text-amber-600" :
                        "bg-blue-50 text-blue-500"
                      }`}>
                        {msg.severity === "critical" ? "Crítico" : msg.severity === "warning" ? "Aviso" : "Info"}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Productos en Riesgo — 3 cols */}
          <div className="col-span-3 bento-card-static p-card-pad">
            <h2 className="card-heading mb-3">En Riesgo</h2>
            <div className="space-y-3">
              {predictions.filter(p => p.minutes_remaining !== null && p.minutes_remaining < 150).map((pred, i) => {
                const urgency = pred.minutes_remaining! < 60 ? "urgent" : "warning";
                return (
                  <div
                    key={pred.sku_id}
                    className={`rounded-xl p-3 border-l-4 animate-slide-in ${
                      urgency === "urgent" ? "border-l-red-500 bg-red-50/50" : "border-l-amber-400 bg-amber-50/50"
                    }`}
                    style={{ animationDelay: `${i * 80}ms` }}
                  >
                    <p className="text-dense-xs font-semibold text-gray-700 truncate">{pred.sku_name}</p>
                    <div className="flex items-center justify-between mt-1.5">
                      <span className="text-[10px] text-gray-400">Stock</span>
                      <span className="text-dense-xs font-bold tabular-nums text-gray-700">{pred.stock_current}/8</span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-[10px] text-gray-400">Se agota en</span>
                      <span className={`text-dense-xs font-bold tabular-nums ${
                        urgency === "urgent" ? "text-red-500" : "text-amber-600"
                      }`}>
                        ~{pred.minutes_remaining} min
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-[10px] text-gray-400">Tendencia</span>
                      <span className="text-[10px]">
                        {pred.trend === "acelerando" ? "🔺 Acelerando" : pred.trend === "desacelerando" ? "🔻 Desacelerando" : "➡️ Estable"}
                      </span>
                    </div>
                  </div>
                );
              })}
              {predictions.filter(p => p.minutes_remaining !== null && p.minutes_remaining < 150).length === 0 && (
                <div className="text-center py-8">
                  <span className="text-2xl">✅</span>
                  <p className="text-dense-xs text-gray-400 mt-2">Sin productos en riesgo</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

/* CameraFeedCard replaced by VideoFeed component — see src/components/VideoFeed.tsx */
