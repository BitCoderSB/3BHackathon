// Tipos base del sistema — Inventario en Tiempo Real Tiendas 3B

// ── Fuentes de cámara ──
export interface CameraSource {
  source_id: string;
  label: string;
  location: string;
  rtsp_url: string;
  status: "online" | "offline" | "reconnecting";
}

export interface StoreConfig {
  store_id: string;
  store_name: string;
  cameras: CameraSource[];
}

// ── Productos e Inventario ──
export interface ProductStock {
  sku_id: string;
  sku_name: string;
  stock_current: number;
  stock_initial: number;
  last_event: string | null;
  alert_active: boolean;
  alert_level: "normal" | "low" | "critical";
  source_id: string;
}

export interface InventoryState {
  timestamp: string;
  products: ProductStock[];
  total_events: number;
  source_id: string;
}

// ── Eventos de detección ──
export interface DetectionEvent {
  event_id: string;
  sku_id: string;
  sku_name: string;
  action: "removed" | "returned";
  stock_before: number;
  stock_after: number;
  timestamp: string;
  source_id: string;
}

// ── Predicciones ──
export interface StockPrediction {
  sku_id: string;
  sku_name: string;
  stock_current: number;
  rate_per_hour: number;
  estimated_depletion: string | null;
  minutes_remaining: number | null;
  trend: "acelerando" | "estable" | "desacelerando";
  confidence: "alta" | "media" | "baja";
  source_id: string;
}

// ── Heatmap ──
export interface HeatmapSlot {
  slot_id: number;
  sku_id: string;
  activity_count: number;
  intensity: number;
}

export interface HeatmapData {
  slots: HeatmapSlot[];
  window_seconds: number;
  last_updated: string;
  source_id: string;
}

// ── Narrativa ──
export interface NarrativeMessage {
  message_id: string;
  severity: "info" | "warning" | "critical";
  text: string;
  sku_id: string | null;
  timestamp: string;
  icon: string;
  source_id: string;
}

// ── Alertas ──
export interface AlertMessage {
  alert_id: string;
  sku_id: string;
  sku_name: string;
  level: "low" | "critical";
  stock_current: number;
  threshold_pct: number;
  message: string;
  timestamp: string;
  source_id: string;
}

// ── Navegación ──
export type ViewId = "live" | "products" | "analytics" | "activity";

export interface NavItem {
  id: ViewId;
  label: string;
  icon: string;
  path: string;
}
