import { NavLink, useLocation } from "react-router-dom";
import { useState } from "react";
import { NAV_ITEMS } from "../mocks/mockData";
import { useSocketContext } from "../hooks/useSocket";

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { cameras, storeName, connected } = useSocketContext();
  const onlineCams = cameras.filter(c => c.status === "online").length;
  const totalCams = cameras.length;

  return (
    <aside
      className={`h-screen sticky top-0 bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-out z-40 ${
        collapsed ? "w-[64px]" : "w-[240px]"
      }`}
    >
      {/* ── Logo + Toggle — skill: header-height 56px ── */}
      <div className="h-[56px] flex items-center justify-between px-3 border-b border-gray-100">
        {!collapsed && (
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 rounded-2xl bg-brand-red flex items-center justify-center flex-shrink-0 shadow-sm">
              <span className="text-white text-base font-bold">3B</span>
            </div>
            <div className="min-w-0">
              <p className="text-dense-sm font-semibold text-gray-900 truncate leading-tight tracking-heading">
                Tiendas 3B
              </p>
              <p className="text-[10px] text-gray-400 font-medium truncate">Inventario en Tiempo Real</p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-9 h-9 rounded-2xl bg-brand-red flex items-center justify-center mx-auto shadow-sm">
            <span className="text-white text-base font-bold">3B</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-7 h-7 rounded-xl hover:bg-surface-page flex items-center justify-center text-gray-400 hover:text-gray-600 transition-all duration-200 flex-shrink-0"
          title={collapsed ? "Expandir" : "Colapsar"}
        >
          <svg className={`w-4 h-4 transition-transform duration-300 ${collapsed ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* ── Sucursal selector ── */}
      {!collapsed && (
        <div className="px-3 py-3 border-b border-gray-100">
          <div className="bg-surface-page rounded-2xl px-3 py-2.5 transition-colors hover:bg-gray-100 cursor-pointer">
            <p className="section-label">Sucursal</p>
            <p className="text-dense-xs font-semibold text-gray-700 truncate mt-0.5">{storeName}</p>
          </div>
        </div>
      )}

      {/* ── Navigation — skill: rounded-xl, brand-red active, hover transitions ── */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <NavLink
              key={item.id}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-2xl transition-all duration-200 group relative ${
                isActive
                  ? "bg-brand-red text-white shadow-md shadow-brand-red/20"
                  : "text-gray-500 hover:bg-surface-page hover:text-gray-800"
              } ${collapsed ? "justify-center px-0" : ""}`}
              title={collapsed ? item.label : undefined}
            >
              <span className={`text-lg flex-shrink-0 transition-transform duration-200 ${!isActive ? "group-hover:scale-110" : ""}`}>
                {item.icon}
              </span>
              {!collapsed && (
                <span className={`text-dense-sm font-medium truncate ${isActive ? "text-white" : ""}`}>
                  {item.label}
                </span>
              )}
              {/* Active indicator dot when collapsed */}
              {collapsed && isActive && (
                <span className="absolute -right-0.5 top-1/2 -translate-y-1/2 w-1 h-4 rounded-l-full bg-brand-red" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ── Footer: skill Real-Time Monitoring → connection status shown ── */}
      <div className={`border-t border-gray-100 px-3 py-3 ${collapsed ? "px-2" : ""}`}>
        {!collapsed ? (
          <div className="space-y-2.5">
            <div className="flex items-center gap-2">
              <span className="connection-dot connection-dot-online" />
              <span className="text-dense-xs font-medium text-gray-600">Sistema activo</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs">📷</span>
                <span className="text-[11px] text-gray-400">{onlineCams}/{totalCams} cámaras</span>
              </div>
              {cameras.map(c => (
                <span
                  key={c.source_id}
                  className={`connection-dot ${
                    c.status === "online" ? "connection-dot-online" :
                    c.status === "reconnecting" ? "connection-dot-reconnecting" :
                    "connection-dot-offline"
                  }`}
                  title={`${c.label}: ${c.status}`}
                />
              ))}
            </div>
            {/* Auto-refresh indicator — skill: Real-Time Monitoring */}
            <div className="flex items-center gap-1.5 opacity-50">
              <svg className="w-3 h-3 text-gray-400 animate-spin" style={{ animationDuration: '3s' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="text-[10px] text-gray-400">Auto-refresh activo</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <span className="connection-dot connection-dot-online" />
            <span className="text-[10px] text-gray-400 font-medium">{onlineCams}/{totalCams}</span>
          </div>
        )}
      </div>
    </aside>
  );
}
