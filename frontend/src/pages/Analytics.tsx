import { useState, useRef, useMemo } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useSocketContext } from "../hooks/useSocket";
import type { StockPrediction, HeatmapSlot, DetectionEvent } from "../types";

/* ── Build timeline data from detection events ── */
const SKU_KEYS: Record<string, string> = {
  agua_burst: "agua_burst",
  burst_energetica_roja: "burst_roja",
  burst_energy: "burst_energy",
  nachos_naturasol: "nachos",
  nebraska_mango: "nebraska",
  sisi_cola: "sisi_cola",
  sun_paradise_naranja: "sun_paradise",
};

function buildTimeline(events: DetectionEvent[]) {
  if (events.length === 0) return [];
  // Sort oldest first
  const sorted = [...events].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  // Group by 5-minute buckets
  const buckets = new Map<string, Record<string, number>>();
  for (const ev of sorted) {
    const d = new Date(ev.timestamp);
    const mins = Math.floor(d.getMinutes() / 5) * 5;
    const key = `${String(d.getHours()).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
    const chartKey = SKU_KEYS[ev.sku_id] || ev.sku_id;
    if (!buckets.has(key)) buckets.set(key, {});
    // Use stock_after as the stock level at that time
    buckets.get(key)![chartKey] = ev.stock_after;
  }
  return Array.from(buckets.entries()).map(([time, data]) => ({ time, ...data }));
}

const TIME_RANGES = [
  { label: "15 min", points: 4 },
  { label: "30 min", points: 6 },
  { label: "1 hora", points: 10 },
];

/* ── Chart series — 7 products with distinct line styles + colors ── */
const CHART_SERIES = [
  { key: "agua_burst",    color: "#3B82F6", dash: undefined,  label: "Agua Burst" },
  { key: "burst_roja",    color: "#EF4444", dash: "4 4",      label: "Burst Roja" },
  { key: "burst_energy",  color: "#EC4899", dash: "8 3",      label: "Burst Energy" },
  { key: "nachos",        color: "#F59E0B", dash: "2 2",      label: "Nachos" },
  { key: "nebraska",      color: "#14B8A6", dash: "6 2 2 2",  label: "Nebraska" },
  { key: "sisi_cola",     color: "#22C55E", dash: "8 4 2 4",  label: "Sisi Cola" },
  { key: "sun_paradise",  color: "#8B5CF6", dash: "6 3",      label: "Sun Paradise" },
];

/* ── Heatmap gradient — monochromatic scale (light → dark red) ── */
function heatmapColor(intensity: number): string {
  // 0 → #FEE2E2 (lightest red) → 1.0 → #991B1B (darkest red)
  const r = Math.round(254 + (153 - 254) * intensity);
  const g = Math.round(226 + (27 - 226) * intensity);
  const b = Math.round(226 + (27 - 226) * intensity);
  return `rgb(${r},${g},${b})`;
}

const CARDS_PER_VIEW = 4;

export default function Analytics() {
  const { predictions, heatmap, events, cameras } = useSocketContext();
  const [camFilter, setCamFilter] = useState<string | "all">("all");
  const [carouselIdx, setCarouselIdx] = useState(0);
  const [timeRange, setTimeRange] = useState(2); // index in TIME_RANGES
  const carouselRef = useRef<HTMLDivElement>(null);

  const heatmapSlots = heatmap?.slots ?? [];
  const timelineAll = useMemo(() => buildTimeline(events), [events]);

  const maxPage = Math.max(0, Math.ceil(predictions.length / CARDS_PER_VIEW) - 1);
  const visiblePredictions = predictions.slice(carouselIdx * CARDS_PER_VIEW, carouselIdx * CARDS_PER_VIEW + CARDS_PER_VIEW);
  const timelineData = timelineAll.slice(-TIME_RANGES[timeRange].points);

  return (
    <div className="p-4 space-y-4">
      {/* ── Header — skill typography ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-heading">Analytics</h1>
          <p className="text-dense-xs text-gray-400 mt-0.5">Predicciones, heatmap y tendencias</p>
        </div>
        <div className="flex gap-1">
          {["all", ...cameras.map(c => c.source_id)].map(id => (
            <button
              key={id}
              onClick={() => setCamFilter(id)}
              className={`pill-toggle ${camFilter === id ? "pill-toggle-active" : "pill-toggle-inactive"}`}
            >
              {id === "all" ? "Todas" : cameras.find(c => c.source_id === id)?.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Predictions carousel — all products ── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-label">Predicciones de Agotamiento</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCarouselIdx(i => Math.max(0, i - 1))}
              disabled={carouselIdx === 0}
              className="w-7 h-7 flex items-center justify-center rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-xs"
            >
              ‹
            </button>
            <span className="text-[10px] text-gray-400 tabular-nums">{carouselIdx + 1}/{maxPage + 1}</span>
            <button
              onClick={() => setCarouselIdx(i => Math.min(maxPage, i + 1))}
              disabled={carouselIdx >= maxPage}
              className="w-7 h-7 flex items-center justify-center rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-xs"
            >
              ›
            </button>
          </div>
        </div>
        <div ref={carouselRef} className="grid grid-cols-2 lg:grid-cols-4 gap-grid-gap">
          {visiblePredictions.map((pred, i) => (
            <PredictionCard key={pred.sku_id} prediction={pred} delay={i * 50} />
          ))}
        </div>
        {/* Dot indicators */}
        <div className="flex justify-center gap-1.5 mt-3">
          {Array.from({ length: maxPage + 1 }, (_, i) => (
            <button
              key={i}
              onClick={() => setCarouselIdx(i)}
              className={`w-1.5 h-1.5 rounded-full transition-all ${i === carouselIdx ? "bg-brand-red w-4" : "bg-gray-300"}`}
            />
          ))}
        </div>
      </div>

      {/* ── Heatmap + Timeline — skill: 12-col grid ── */}
      <div className="grid grid-cols-12 gap-grid-gap">
        {/* Heatmap — skill: cool→hot gradient + numeric legend */}
        <div className="col-span-5 bento-card-static p-card-pad">
          <div className="flex items-center justify-between mb-3">
            <h2 className="card-heading">Mapa de Calor</h2>
            <span className="text-[10px] text-gray-400">Últimos 5 min</span>
          </div>
          <div className="grid grid-cols-4 gap-1.5">
            {heatmapSlots.map(slot => (
              <HeatmapCell key={slot.slot_id} slot={slot} />
            ))}
          </div>
          {/* Numeric color legend — skill: Heatmap always include numeric color legend */}
          <div className="flex items-center gap-2 mt-3">
            <span className="text-[9px] text-gray-400 tabular-nums">0</span>
            <div className="flex-1 flex gap-px">
              {Array.from({ length: 10 }, (_, i) => (
                <div
                  key={i}
                  className="flex-1 h-2 first:rounded-l last:rounded-r"
                  style={{ backgroundColor: heatmapColor(i / 9) }}
                />
              ))}
            </div>
            <span className="text-[9px] text-gray-400 tabular-nums">Max</span>
          </div>
        </div>

        {/* Timeline Chart — 7 products, adjustable range */}
        <div className="col-span-7 bento-card-static p-card-pad">
          <div className="flex items-center justify-between mb-3">
            <h2 className="card-heading">Línea de Tiempo — Stock</h2>
            <div className="flex items-center gap-3">
              {/* Time range selector */}
              <div className="flex gap-0.5">
                {TIME_RANGES.map((r, i) => (
                  <button
                    key={r.label}
                    onClick={() => setTimeRange(i)}
                    className={`px-2 py-0.5 text-[10px] rounded-md transition-all ${
                      timeRange === i ? "bg-brand-red text-white font-semibold" : "text-gray-400 hover:bg-gray-100"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {/* Legend — all 7 series visible */}
          <div className="flex items-center gap-2 flex-wrap mb-2">
            {CHART_SERIES.map(s => (
              <div key={s.key} className="flex items-center gap-1">
                <svg width="16" height="8">
                  <line
                    x1="0" y1="4" x2="16" y2="4"
                    stroke={s.color} strokeWidth="2"
                    strokeDasharray={s.dash || "none"}
                  />
                </svg>
                <span className="text-[9px] text-gray-400">{s.label}</span>
              </div>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#9CA3AF" }} />
              <YAxis tick={{ fontSize: 10, fill: "#9CA3AF" }} domain={[0, 8]} width={24} />
              <Tooltip
                contentStyle={{ fontSize: 11, borderRadius: 16, border: "1px solid #E5E7EB", boxShadow: "0 4px 6px rgba(0,0,0,0.05)" }}
                labelStyle={{ fontWeight: 600 }}
              />
              {CHART_SERIES.map(s => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  stroke={s.color}
                  fill={s.color}
                  fillOpacity={0.08}
                  strokeWidth={2}
                  strokeDasharray={s.dash}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Events Table — skill: data-table, 36px rows, sticky headers ── */}
      <div className="bento-card-static overflow-hidden">
        <div className="px-card-pad pt-3 pb-2 border-b border-gray-100">
          <h2 className="card-heading">Últimos Eventos de Detección</h2>
        </div>
        <div className="data-table overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left">Hora</th>
                <th className="text-left">Producto</th>
                <th className="text-left">Acción</th>
                <th className="text-left">Stock</th>
                <th className="text-left">Cámara</th>
              </tr>
            </thead>
            <tbody>
              {events.map(ev => (
                <tr key={ev.event_id}>
                  <td className="text-gray-500 font-mono tabular-nums">
                    {new Date(ev.timestamp).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </td>
                  <td className="font-medium text-gray-700">{ev.sku_name}</td>
                  <td>
                    <span className={`status-badge ${
                      ev.action === "removed" ? "bg-status-red/10 text-status-red" : "bg-status-green/10 text-status-green"
                    }`}>
                      {ev.action === "removed" ? "↓ Retirado" : "↑ Devuelto"}
                    </span>
                  </td>
                  <td className="text-gray-600 font-mono tabular-nums">{ev.stock_before} → {ev.stock_after}</td>
                  <td className="text-gray-400">{ev.source_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ── Prediction Card — skill: kpi-card + urgency border + count-up ── */
function PredictionCard({ prediction, delay }: { prediction: StockPrediction; delay: number }) {
  const urgency = prediction.minutes_remaining !== null && prediction.minutes_remaining < 60
    ? "urgent" : prediction.minutes_remaining !== null && prediction.minutes_remaining < 120
    ? "warning" : "normal";

  const borderColor = urgency === "urgent" ? "border-l-critical" : urgency === "warning" ? "border-l-status-yellow" : "border-l-status-green";
  const trendIcon = prediction.trend === "acelerando" ? "🔺" : prediction.trend === "desacelerando" ? "🔻" : "➡️";

  return (
    <div
      className={`bento-card-static p-card-pad border-l-4 ${borderColor} animate-slide-in`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between mb-2">
        <p className="text-dense-xs font-semibold text-gray-700 leading-tight line-clamp-2">{prediction.sku_name}</p>
        <span className="text-sm flex-shrink-0">{trendIcon}</span>
      </div>
      <div className="space-y-1">
        {[
          { label: "Stock actual", value: `${prediction.stock_current}/8`, bold: false },
          { label: "Ritmo", value: `${prediction.rate_per_hour}/hr`, bold: false },
          {
            label: "Se agota en",
            value: prediction.minutes_remaining !== null ? `~${prediction.minutes_remaining} min` : "—",
            bold: true,
            color: urgency === "urgent" ? "text-critical" : urgency === "warning" ? "text-status-yellow" : ""
          },
        ].map(row => (
          <div key={row.label} className="flex items-center justify-between">
            <span className="text-[10px] text-gray-400">{row.label}</span>
            <span className={`text-dense-xs ${row.bold ? "font-bold" : "font-medium"} ${row.color || "text-gray-700"} tabular-nums`}>
              {row.value}
            </span>
          </div>
        ))}
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-gray-400">Confianza</span>
          <span className={`status-badge text-[9px] ${
            prediction.confidence === "alta" ? "bg-status-green/10 text-status-green" :
            prediction.confidence === "media" ? "bg-status-yellow/10 text-status-yellow" :
            "bg-gray-100 text-gray-500"
          }`}>
            {prediction.confidence}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ── Heatmap Cell — monochromatic red scale ── */
function HeatmapCell({ slot }: { slot: HeatmapSlot }) {
  const bgColor = heatmapColor(slot.intensity);
  const textDark = slot.intensity > 0.5;
  const rawName = slot.sku_id.replace(/_/g, " ");
  const displayName = rawName.length > 12 ? rawName.slice(0, 12) + "..." : rawName;

  return (
    <div
      className="rounded-xl p-2.5 flex flex-col items-center justify-center min-h-[64px] transition-all duration-300 hover:scale-105"
      style={{ backgroundColor: bgColor }}
      title={rawName}
    >
      <span className={`text-dense-xs font-bold ${textDark ? "text-white" : "text-gray-800"}`}>
        {slot.activity_count}
      </span>
      <span className={`text-[8px] text-center leading-tight mt-0.5 ${textDark ? "text-white/80" : "text-gray-500"}`}>
        {displayName}
      </span>
    </div>
  );
}
