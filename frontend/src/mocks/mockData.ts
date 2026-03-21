import type { StoreConfig, ProductStock, StockPrediction, HeatmapData, NarrativeMessage, DetectionEvent, NavItem } from "../types";

// ── Configuración de tienda demo ──
export const MOCK_STORE: StoreConfig = {
  store_id: "store-demo",
  store_name: "Sucursal Demo — Hackathon",
  cameras: [
    {
      source_id: "cam-1",
      label: "Cámara 1",
      location: "Anaquel Bebidas",
      rtsp_url: "rtsp://admin:admin1234@172.31.13.190:554/cam/realmonitor?channel=1&subtype=0",
      status: "online",
    },
    {
      source_id: "cam-2",
      label: "Cámara 2",
      location: "Anaquel Snacks",
      rtsp_url: "rtsp://admin:admin1234@172.31.13.191:554/cam/realmonitor?channel=1&subtype=0",
      status: "online",
    },
  ],
};

// ── Productos por cámara ──
const BASE_PRODUCTS: Omit<ProductStock, "source_id">[] = [
  { sku_id: "agua_burst", sku_name: "Agua Natural Burst 1500ml", stock_current: 7, stock_initial: 8, last_event: null, alert_active: false, alert_level: "normal" },
  { sku_id: "burst_energetica_roja", sku_name: "Bebida Energetica Red Burst 473ml", stock_current: 5, stock_initial: 8, last_event: null, alert_active: false, alert_level: "normal" },
  { sku_id: "burst_energy", sku_name: "Bebida Energetica Original Burst Energy 600ml", stock_current: 8, stock_initial: 8, last_event: null, alert_active: false, alert_level: "normal" },
  { sku_id: "nachos_naturasol", sku_name: "Nachos Con Sal Naturasol 200gr", stock_current: 2, stock_initial: 8, last_event: "2026-03-21T14:32:00Z", alert_active: true, alert_level: "critical" },
  { sku_id: "nebraska_mango", sku_name: "Bebida Mango-Durazno Nebraska 460ml", stock_current: 6, stock_initial: 8, last_event: null, alert_active: false, alert_level: "normal" },
  { sku_id: "sisi_cola", sku_name: "Refresco Cola Sin Azucar Sisi 355ml", stock_current: 4, stock_initial: 8, last_event: null, alert_active: false, alert_level: "low" },
  { sku_id: "sun_paradise_naranja", sku_name: "Bebida Naranja Sun Paradise 900ml", stock_current: 3, stock_initial: 8, last_event: null, alert_active: true, alert_level: "low" },
];

export const MOCK_PRODUCTS_CAM1: ProductStock[] = BASE_PRODUCTS.map(p => ({ ...p, source_id: "cam-1" }));
export const MOCK_PRODUCTS_CAM2: ProductStock[] = BASE_PRODUCTS.map(p => ({
  ...p,
  source_id: "cam-2",
  stock_current: Math.min(p.stock_initial, p.stock_current + Math.floor(Math.random() * 3)),
}));

export const ALL_MOCK_PRODUCTS: ProductStock[] = [...MOCK_PRODUCTS_CAM1, ...MOCK_PRODUCTS_CAM2];

// ── Predicciones mock ──
export const MOCK_PREDICTIONS: StockPrediction[] = [
  { sku_id: "nachos_naturasol", sku_name: "Nachos Con Sal Naturasol 200gr", stock_current: 2, rate_per_hour: 3.5, estimated_depletion: "2026-03-21T15:06:00Z", minutes_remaining: 34, trend: "acelerando", confidence: "alta", source_id: "cam-1" },
  { sku_id: "sun_paradise_naranja", sku_name: "Bebida Naranja Sun Paradise 900ml", stock_current: 3, rate_per_hour: 2.1, estimated_depletion: "2026-03-21T15:57:00Z", minutes_remaining: 86, trend: "estable", confidence: "media", source_id: "cam-1" },
  { sku_id: "sisi_cola", sku_name: "Refresco Cola Sin Azucar Sisi 355ml", stock_current: 4, rate_per_hour: 1.8, estimated_depletion: "2026-03-21T16:30:00Z", minutes_remaining: 133, trend: "desacelerando", confidence: "media", source_id: "cam-1" },
  { sku_id: "burst_energetica_roja", sku_name: "Bebida Energetica Red Burst 473ml", stock_current: 5, rate_per_hour: 1.2, estimated_depletion: null, minutes_remaining: 250, trend: "estable", confidence: "baja", source_id: "cam-1" },
  { sku_id: "agua_burst", sku_name: "Agua Natural Burst 1500ml", stock_current: 7, rate_per_hour: 0.8, estimated_depletion: null, minutes_remaining: 525, trend: "estable", confidence: "baja", source_id: "cam-1" },
  { sku_id: "burst_energy", sku_name: "Bebida Energetica Original Burst Energy 600ml", stock_current: 8, rate_per_hour: 0.4, estimated_depletion: null, minutes_remaining: null, trend: "estable", confidence: "baja", source_id: "cam-1" },
  { sku_id: "nebraska_mango", sku_name: "Bebida Mango-Durazno Nebraska 460ml", stock_current: 6, rate_per_hour: 1.0, estimated_depletion: null, minutes_remaining: 360, trend: "desacelerando", confidence: "media", source_id: "cam-1" },
];

// ── Heatmap mock ──
export const MOCK_HEATMAP: HeatmapData = {
  slots: [
    { slot_id: 0, sku_id: "agua_burst", activity_count: 3, intensity: 0.38 },
    { slot_id: 1, sku_id: "burst_energetica_roja", activity_count: 5, intensity: 0.63 },
    { slot_id: 2, sku_id: "burst_energy", activity_count: 1, intensity: 0.13 },
    { slot_id: 3, sku_id: "nachos_naturasol", activity_count: 8, intensity: 1.0 },
    { slot_id: 4, sku_id: "nebraska_mango", activity_count: 2, intensity: 0.25 },
    { slot_id: 5, sku_id: "sisi_cola", activity_count: 4, intensity: 0.50 },
    { slot_id: 6, sku_id: "sun_paradise_naranja", activity_count: 6, intensity: 0.75 },
  ],
  window_seconds: 300,
  last_updated: new Date().toISOString(),
  source_id: "cam-1",
};

// ── Narrativas mock ──
export const MOCK_NARRATIVES: NarrativeMessage[] = [
  { message_id: "n1", severity: "info", text: "Se retiró 1 unidad de Agua Natural Burst 1500ml", sku_id: "agua_burst", timestamp: "2026-03-21T14:20:00Z", icon: "📦", source_id: "cam-1" },
  { message_id: "n2", severity: "info", text: "Se retiró 1 unidad de Bebida Energetica Red Burst 473ml", sku_id: "burst_energetica_roja", timestamp: "2026-03-21T14:22:15Z", icon: "📦", source_id: "cam-1" },
  { message_id: "n3", severity: "warning", text: "Nachos Con Sal Naturasol 200gr se agotará en ~34 minutos", sku_id: "nachos_naturasol", timestamp: "2026-03-21T14:28:00Z", icon: "⏱️", source_id: "cam-1" },
  { message_id: "n4", severity: "critical", text: "⚠️ ALERTA: Nachos Con Sal Naturasol 200gr stock bajo (2/8 = 25%)", sku_id: "nachos_naturasol", timestamp: "2026-03-21T14:32:00Z", icon: "🔔", source_id: "cam-1" },
  { message_id: "n5", severity: "info", text: "Se devolvió 1 unidad de Bebida Energetica Red Burst 473ml", sku_id: "burst_energetica_roja", timestamp: "2026-03-21T14:33:10Z", icon: "↩️", source_id: "cam-2" },
  { message_id: "n6", severity: "info", text: "Se retiró 1 unidad de Refresco Cola Sin Azucar Sisi 355ml", sku_id: "sisi_cola", timestamp: "2026-03-21T14:35:45Z", icon: "📦", source_id: "cam-2" },
];

// ── Eventos mock ──
export const MOCK_EVENTS: DetectionEvent[] = [
  { event_id: "e1", sku_id: "agua_burst", sku_name: "Agua Natural Burst 1500ml", action: "removed", stock_before: 8, stock_after: 7, timestamp: "2026-03-21T14:20:00Z", source_id: "cam-1" },
  { event_id: "e2", sku_id: "burst_energetica_roja", sku_name: "Bebida Energetica Red Burst 473ml", action: "removed", stock_before: 6, stock_after: 5, timestamp: "2026-03-21T14:22:15Z", source_id: "cam-1" },
  { event_id: "e3", sku_id: "nachos_naturasol", sku_name: "Nachos Con Sal Naturasol 200gr", action: "removed", stock_before: 3, stock_after: 2, timestamp: "2026-03-21T14:32:00Z", source_id: "cam-1" },
  { event_id: "e4", sku_id: "burst_energetica_roja", sku_name: "Bebida Energetica Red Burst 473ml", action: "returned", stock_before: 5, stock_after: 6, timestamp: "2026-03-21T14:33:10Z", source_id: "cam-2" },
  { event_id: "e5", sku_id: "sisi_cola", sku_name: "Refresco Cola Sin Azucar Sisi 355ml", action: "removed", stock_before: 5, stock_after: 4, timestamp: "2026-03-21T14:35:45Z", source_id: "cam-2" },
];

// ── Navegación del sidebar ──
export const NAV_ITEMS: NavItem[] = [
  { id: "live", label: "Panel en Vivo", icon: "📹", path: "/" },
  { id: "products", label: "Productos", icon: "📦", path: "/products" },
  { id: "analytics", label: "Analytics", icon: "📊", path: "/analytics" },
  { id: "activity", label: "Actividad", icon: "📋", path: "/activity" },
];
