import { useState, useMemo } from "react";
import { useSocketContext } from "../hooks/useSocket";
import type { ProductStock } from "../types";

/* ── Semi-circle tick gauge — configurable params ── */
// MANUAL TUNING: adjust these defaults to control the gauge appearance
//   ticks       → number of segments (fewer = bigger segments)
//   strokeW     → thickness of each tick line
//   gap         → angular gap in radians subtracted between ticks (higher = more space)
//   rInner/rOuter → inner/outer radius of the arc
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

/* ── Product image by sku — maps to /products/ static images ── */
const PRODUCT_IMAGES: Record<string, string> = {
  agua_burst: "/products/agua-burst.jpg",
  burst_energetica_roja: "/products/burst-sports-ponche-de-frutas-1.jpg",
  burst_energy: "/products/burst-energy-mora-azull.jpg",
  nachos_naturasol: "/products/nachos.jpg",
  nebraska_mango: "/products/26449-Bebida-Mango-Durazno-Nebraska-02.jpg",
  sisi_cola: "/products/22287-sisi-cola-sin-azucar.jpg",
  sun_paradise_naranja: "/products/render-citrus-punch-sunparadise-3l-1.jpg",
};

function productImage(sku: string) {
  return PRODUCT_IMAGES[sku] || "/products/agua-burst.jpg";
}

export default function ProductCatalog() {
  const { products, cameras } = useSocketContext();
  const [search, setSearch] = useState("");
  const [camFilter, setCamFilter] = useState<string | "all">("all");
  const [sortBy, setSortBy] = useState<"name" | "stock" | "alert">("name");

  const filtered = useMemo(() => {
    let list: ProductStock[] = camFilter === "all"
      ? products
      : products.filter(p => p.source_id === camFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(p => p.sku_name.toLowerCase().includes(q) || p.sku_id.toLowerCase().includes(q));
    }
    return [...list].sort((a, b) => {
      if (sortBy === "stock") return a.stock_current - b.stock_current;
      if (sortBy === "alert") return (b.alert_active ? 1 : 0) - (a.alert_active ? 1 : 0);
      return a.sku_name.localeCompare(b.sku_name);
    });
  }, [search, camFilter, sortBy, products]);

  const totalActive = filtered.length;
  const mostSold = [...filtered].sort((a, b) =>
    (b.stock_initial - b.stock_current) - (a.stock_initial - a.stock_current)
  )[0];
  const avgPct = filtered.length > 0
    ? Math.round(filtered.reduce((s, p) => s + (p.stock_current / p.stock_initial) * 100, 0) / filtered.length)
    : 0;
  const totalUnits = filtered.reduce((s, p) => s + p.stock_current, 0);

  return (
    <div className="space-y-0">
      {/* ── Top section — white full-width card ── */}
      <div className="bg-white w-full px-6 py-4">
        {/* Header + Search + Camera toggle */}
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="page-heading flex-shrink-0" style={{ fontSize: '30px' }}>Catálogo de Productos</h1>
          <div className="flex items-center gap-3 flex-1">
            <input
              type="text"
              placeholder="Buscar producto..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="flex-1 px-3 py-1.5 text-dense-sm border border-gray-200 rounded-md bg-[#F5F5F5] focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red focus:bg-white transition-colors"
            />
            <div className="h-5 w-px bg-gray-200" />
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
        </div>

        {/* KPI Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-center mt-6 pt-5 border-t border-gray-100 gap-4 sm:gap-8">
        {/* Productos Activos */}
        <div className="flex flex-col">
          <span className="text-[13px] text-[#8A8A8A]">Productos Activos</span>
          <span className="text-[26px] font-semibold text-[#1A1A1A] leading-tight tabular-nums">{totalActive}</span>
        </div>

        <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
        <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

        {/* Más Vendido */}
        <div className="flex flex-col">
          <span className="text-[13px] text-[#8A8A8A]">Más Vendido</span>
          <div className="flex items-center gap-2 mt-0.5">
            {mostSold && (
              <img
                src={productImage(mostSold.sku_id)}
                alt=""
                className="w-7 h-7 rounded-lg object-contain border border-gray-100"
              />
            )}
            <span className="text-[22px] font-semibold text-[#1A1A1A] leading-tight truncate max-w-[140px]">
              {mostSold ? mostSold.sku_name.split(" ").slice(0, 2).join(" ") : "—"}
            </span>
          </div>
        </div>

        <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
        <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

        {/* Disponibilidad */}
        <div className="flex flex-col">
          <span className="text-[13px] text-[#8A8A8A]">Disponibilidad</span>
          <div className="flex items-center gap-2 mt-0.5">
            <SemiCircleGauge current={avgPct} initial={100} />
            <span className={`text-[14px] font-bold leading-tight ${
              avgPct <= 25 ? 'text-red-500' : avgPct <= 50 ? 'text-yellow-500' : 'text-green-500'
            }`}>
              {avgPct <= 25 ? 'Crítico' : avgPct <= 50 ? 'Bajo' : 'Bueno'}
            </span>
          </div>
        </div>

        <div className="hidden sm:block w-px self-stretch bg-[#E5E5E5]" style={{ height: '60%', alignSelf: 'center' }} />
        <div className="sm:hidden h-px w-full bg-[#E5E5E5]" />

        {/* Unidades Totales */}
        <div className="flex flex-col">
          <span className="text-[13px] text-[#8A8A8A]">Unidades Totales</span>
          <span className="text-[26px] font-semibold text-[#1A1A1A] leading-tight tabular-nums">{totalUnits}</span>
        </div>
        </div>
      </div>

      {/* ── Bottom section — full-width background card ── */}
      <div className="w-full px-6 py-4" style={{ backgroundColor: 'rgba(249, 249, 249, 1)' }}>
        {/* Sort buttons */}
        <div className="flex items-center gap-1 mb-2.5">
          {([["name", "A-Z"], ["stock", "Stock ↑"], ["alert", "Alertas"]] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSortBy(key)}
              className={`pill-toggle ${sortBy === key ? "pill-toggle-active !bg-gray-900 !text-white" : "pill-toggle-inactive"}`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Product Table */}
        <div className="bg-white border border-gray-100 overflow-hidden" style={{ borderRadius: '16px' }}>
        <div className="data-table overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="pl-3 pr-1" style={{ width: 56 }}></th>
                <th className="text-center" style={{ width: '40%' }}>Producto</th>
                <th className="text-center border-l border-gray-100" style={{ width: '20%' }}>Stock</th>
                <th className="text-center border-l border-gray-100" style={{ width: '20%' }}>Nivel</th>
                <th className="text-center border-l border-gray-100" style={{ width: '20%' }}>Estado</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((product, idx) => {
                const pct = Math.round((product.stock_current / product.stock_initial) * 100);
                return (
                  <tr
                    key={product.sku_id + product.source_id}
                    className={`animate-slide-in ${product.alert_active ? "!bg-status-red/[0.03]" : ""}`}
                    style={{ animationDelay: `${idx * 30}ms` }}
                  >
                    <td className="pl-3 pr-1">
                      <div className="w-10 h-10 rounded-xl bg-white border border-gray-100 overflow-hidden flex items-center justify-center p-0.5">
                        <img
                          src={productImage(product.sku_id)}
                          alt={product.sku_name}
                          className="w-full h-full object-contain"
                        />
                      </div>
                    </td>
                    <td>
                      <p className="text-dense-sm font-semibold text-gray-800 truncate max-w-[260px]">{product.sku_name}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">
                        {product.sku_id}
                        {camFilter === "all" && <span className="ml-1.5 text-gray-300">📷 {product.source_id}</span>}
                      </p>
                    </td>
                    <td className="text-center border-l border-gray-100">
                      <div className="flex flex-col items-center gap-0.5">
                        <span className="text-[9px] font-medium uppercase text-gray-400 tracking-wide">Stock</span>
                        <img src="/cart-fill.svg" alt="" className="w-4 h-4 opacity-40" />
                        <span className="text-[13px] font-bold text-gray-700 tabular-nums leading-none">
                          {product.stock_current}<span className="font-bold">/</span>{product.stock_initial}
                        </span>
                      </div>
                    </td>
                    <td className="border-l border-gray-100">
                      <div className="flex items-center justify-center">
                        <SemiCircleGauge current={product.stock_current} initial={product.stock_initial} />
                      </div>
                    </td>
                    <td className="text-center border-l border-gray-100">
                      <span className={`status-badge ${
                        product.alert_level === "critical" ? "bg-status-red/10 text-status-red" :
                        product.alert_level === "low" ? "bg-status-yellow/10 text-status-yellow" :
                        "bg-status-green/10 text-status-green"
                      }`}>
                        {product.alert_active && <span className="connection-dot connection-dot-online bg-current" />}
                        {product.alert_level === "critical" ? "Crítico" :
                         product.alert_level === "low" ? "Bajo" : "Normal"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        </div>
      </div>
    </div>
  );
}
