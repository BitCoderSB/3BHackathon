import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MOCK_STORE, MOCK_PRODUCTS_CAM1, MOCK_PRODUCTS_CAM2, MOCK_NARRATIVES } from "../mocks/mockData";
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
  const [selectedCam, setSelectedCam] = useState<string | "all">("all");
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());
  const cameras = MOCK_STORE.cameras;

  const products = selectedCam === "all"
    ? MOCK_PRODUCTS_CAM1
    : selectedCam === "cam-1" ? MOCK_PRODUCTS_CAM1 : MOCK_PRODUCTS_CAM2;

  const alerts = MOCK_NARRATIVES.filter(n => n.severity === "critical" || n.severity === "warning");
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
              <span className="connection-dot connection-dot-online" />
              <span className="text-[10px] font-medium">Conectado</span>
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
          <div className="flex flex-col">
            <span className="text-[13px] text-[#8A8A8A]">Productos</span>
            <span className="text-[26px] font-semibold text-[#1A1A1A] leading-tight tabular-nums">{totalProducts}</span>
          </div>

          <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
          <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

          {/* Disponibilidad — with SemiCircleGauge */}
          <div className="flex flex-col">
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
          <div className="flex flex-col">
            <span className="text-[13px] text-[#8A8A8A]">Alertas Activas</span>
            <span className={`text-[26px] font-semibold leading-tight tabular-nums ${
              alertCount > 0 ? 'text-red-500' : 'text-[#1A1A1A]'
            }`}>{alertCount}</span>
          </div>

          <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
          <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

          {/* Cámaras Online */}
          <div className="flex flex-col">
            <span className="text-[13px] text-[#8A8A8A]">Cámaras Online</span>
            <span className="text-[26px] font-semibold text-[#1A1A1A] leading-tight tabular-nums">{cameras.filter(c => c.status === "online").length}/{cameras.length}</span>
          </div>
        </div>
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
                <CameraFeedCard key={cam.source_id} label={cam.label} location={cam.location} status={cam.status} />
              ))}
            </div>
          ) : (
            <CameraFeedCard
              label={cameras.find(c => c.source_id === selectedCam)!.label}
              location={cameras.find(c => c.source_id === selectedCam)!.location}
              status={cameras.find(c => c.source_id === selectedCam)!.status}
              large
            />
          )}
        </div>

        {/* Stock Panel — 4 cols, skill: Data-Dense compact, 36px rows */}
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
          {/* Progress overview bar — skill: Gauge → Red→Yellow→Green */}
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-4">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                pctAvail > 70 ? "bg-status-green" : pctAvail > 40 ? "bg-status-yellow" : "bg-status-red"
              }`}
              style={{ width: `${pctAvail}%` }}
            />
          </div>
          <div className="flex-1 space-y-0.5 overflow-y-auto">
            {products.map(p => (
              <StockBar key={p.sku_id + p.source_id} product={p} />
            ))}
          </div>
        </div>
      </div>

      </div>
    </div>
  );
}

/* ── Camera Feed Card — skill: Real-Time Monitoring → live indicator, connection status ── */
function CameraFeedCard({ label, location, status, large }: { label: string; location: string; status: string; large?: boolean }) {
  return (
    <div className={`bento-card overflow-hidden ${large ? "min-h-[420px]" : "min-h-[260px]"} animate-slide-in`}>
      <div className="px-card-pad pt-3 pb-2 flex items-center justify-between border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className={`connection-dot ${status === "online" ? "connection-dot-online" : "connection-dot-offline"}`} />
          <h3 className="card-heading">{label}</h3>
          <span className="section-label normal-case">— {location}</span>
        </div>
        <div className="live-badge">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse-live" />
          EN VIVO
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100/50 p-8">
        <div className="text-center">
          <div className="w-16 h-16 rounded-3xl bg-gray-200/80 flex items-center justify-center mx-auto mb-3">
            <span className="text-2xl text-gray-400">📷</span>
          </div>
          <p className="text-dense-sm font-medium text-gray-400">{label}</p>
          <p className="text-dense-xs text-gray-300 mt-1">
            {status === "online" ? "Esperando stream del backend..." : "Cámara desconectada"}
          </p>
        </div>
      </div>
    </div>
  );
}
