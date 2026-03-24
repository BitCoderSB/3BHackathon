import { useEffect, useState, useRef, useCallback, createContext, useContext } from "react";
import { io, Socket } from "socket.io-client";
import type {
  ProductStock,
  DetectionEvent,
  StockPrediction,
  HeatmapData,
  NarrativeMessage,
  AlertMessage,
  CameraSource,
} from "../types";
import {
  MOCK_PRODUCTS_CAM1,
  MOCK_PREDICTIONS,
  MOCK_HEATMAP,
  MOCK_NARRATIVES,
  MOCK_EVENTS,
  MOCK_STORE,
} from "../mocks/mockData";

// ── Adaptador: convierte ProductStock del backend al tipo frontend ──
function adaptProduct(p: Record<string, unknown>): ProductStock {
  const stockCurrent = (p.stock_current as number) ?? 0;
  const stockInitial = (p.stock_initial as number) ?? 8;
  const pct = stockInitial > 0 ? stockCurrent / stockInitial : 1;
  const alertActive = (p.is_alert as boolean) ?? (p.alert_active as boolean) ?? false;
  const alertLevel: ProductStock["alert_level"] =
    (p.alert_level as ProductStock["alert_level"]) ??
    (pct <= 0.25 ? "critical" : pct <= 0.5 ? "low" : "normal");
  return {
    sku_id: (p.sku_id as string) ?? "",
    sku_name: (p.sku_name as string) ?? "",
    stock_current: stockCurrent,
    stock_initial: stockInitial,
    last_event: (p.last_event as string) ?? null,
    alert_active: alertActive,
    alert_level: alertLevel,
    source_id: (p.source_id as string) ?? "cam-1",
  };
}

// ── Estado global del socket ──
export interface SocketState {
  connected: boolean;
  products: ProductStock[];
  events: DetectionEvent[];
  predictions: StockPrediction[];
  heatmap: HeatmapData | null;
  narratives: NarrativeMessage[];
  alerts: AlertMessage[];
  videoFrame: string | null;
  usingMock: boolean;
  cameras: CameraSource[];
  storeName: string;
}

const INITIAL_STATE: SocketState = {
  connected: false,
  products: [],
  events: [],
  predictions: [],
  heatmap: null,
  narratives: [],
  alerts: [],
  videoFrame: null,
  usingMock: true,
  cameras: MOCK_STORE.cameras,
  storeName: MOCK_STORE.store_name,
};

const BACKEND_URL = "http://localhost:8000";
const CONNECT_TIMEOUT_MS = 3_000;
const MAX_NARRATIVES = 50;
const MAX_EVENTS = 100;

// ── Context ──
const SocketContext = createContext<SocketState>(INITIAL_STATE);

export function useSocketContext() {
  return useContext(SocketContext);
}

export { SocketContext };

// ── Hook principal ──
export function useSocket(): SocketState {
  const [state, setState] = useState<SocketState>({
    ...INITIAL_STATE,
    // Arrancar con datos mock mientras intenta conectar
    products: MOCK_PRODUCTS_CAM1,
    predictions: MOCK_PREDICTIONS,
    heatmap: MOCK_HEATMAP,
    narratives: MOCK_NARRATIVES,
    events: MOCK_EVENTS,
    usingMock: true,
  });

  const socketRef = useRef<Socket | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Helper para cargar estado inicial desde REST al conectar
  const fetchInitialState = useCallback(async () => {
    try {
      const [invRes, predRes, hmRes, narrRes, evtRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/inventory`),
        fetch(`${BACKEND_URL}/api/predictions`),
        fetch(`${BACKEND_URL}/api/heatmap`),
        fetch(`${BACKEND_URL}/api/narratives?limit=50`),
        fetch(`${BACKEND_URL}/api/events?limit=50`),
      ]);
      const [inv, preds, hm, narrs, evts] = await Promise.all([
        invRes.json(),
        predRes.json(),
        hmRes.json(),
        narrRes.json(),
        evtRes.json(),
      ]);

      const products: ProductStock[] = Array.isArray(inv.products)
        ? inv.products.map((p: Record<string, unknown>) => adaptProduct(p))
        : [];

      setState((prev) => ({
        ...prev,
        products: products.length > 0 ? products : prev.products,
        predictions: Array.isArray(preds) ? preds : prev.predictions,
        heatmap: hm ?? prev.heatmap,
        narratives: Array.isArray(narrs) ? narrs : prev.narratives,
        events: Array.isArray(evts) ? evts : prev.events,
        usingMock: false,
      }));
    } catch {
      // Si falla REST, mantener datos mock
      console.warn("[useSocket] No se pudo obtener estado inicial por REST");
    }
  }, []);

  useEffect(() => {
    const socket = io(BACKEND_URL, {
      transports: ["websocket", "polling"],
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
      timeout: CONNECT_TIMEOUT_MS,
    });

    socketRef.current = socket;

    // Timeout de conexión → fallback a mock
    timeoutRef.current = setTimeout(() => {
      if (!socket.connected) {
        console.info("[useSocket] Timeout de conexión — usando datos mock");
        setState((prev) => ({ ...prev, usingMock: true }));
      }
    }, CONNECT_TIMEOUT_MS);

    // ── Eventos de conexión ──
    socket.on("connect", () => {
      console.info("[useSocket] Conectado al backend");
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setState((prev) => ({ ...prev, connected: true, usingMock: false }));
      fetchInitialState();
    });

    socket.on("disconnect", () => {
      console.warn("[useSocket] Desconectado del backend");
      setState((prev) => ({ ...prev, connected: false }));
    });

    socket.on("connect_error", () => {
      console.warn("[useSocket] Error de conexión");
    });

    // ── Eventos de datos ──
    socket.on("inventory_update", (data: { event?: unknown; stock?: Record<string, unknown> }) => {
      if (data.stock) {
        const adapted = adaptProduct(data.stock);
        setState((prev) => {
          const exists = prev.products.some((p) => p.sku_id === adapted.sku_id);
          const updated = prev.products.map((p) =>
            p.sku_id === adapted.sku_id ? { ...p, ...adapted } : p
          );
          return {
            ...prev,
            products: exists ? updated : [...prev.products, adapted],
          };
        });
      }
    });

    socket.on("detection_event", (data: DetectionEvent) => {
      setState((prev) => ({
        ...prev,
        events: [data, ...prev.events].slice(0, MAX_EVENTS),
      }));
    });

    socket.on("video_frame", (data: { frame: string }) => {
      setState((prev) => ({ ...prev, videoFrame: data.frame }));
    });

    socket.on("prediction_update", (data: { data: StockPrediction }) => {
      if (data.data) {
        setState((prev) => {
          const idx = prev.predictions.findIndex((p) => p.sku_id === data.data.sku_id);
          const updated = [...prev.predictions];
          if (idx >= 0) {
            updated[idx] = data.data;
          } else {
            updated.push(data.data);
          }
          return { ...prev, predictions: updated };
        });
      }
    });

    socket.on("heatmap_update", (data: { data: HeatmapData }) => {
      if (data.data) {
        setState((prev) => ({ ...prev, heatmap: data.data }));
      }
    });

    socket.on("narrative", (data: { data: NarrativeMessage }) => {
      if (data.data) {
        setState((prev) => ({
          ...prev,
          narratives: [data.data, ...prev.narratives].slice(0, MAX_NARRATIVES),
        }));
      }
    });

    socket.on("alert", (data: AlertMessage | { event?: unknown; stock?: Record<string, unknown> }) => {
      setState((prev) => {
        const stockRaw = (data as { stock?: Record<string, unknown> }).stock;
        let products = prev.products;
        if (stockRaw) {
          const adapted = adaptProduct(stockRaw);
          products = prev.products.map((p) =>
            p.sku_id === adapted.sku_id
              ? { ...p, ...adapted, alert_active: true }
              : p
          );
        }
        return {
          ...prev,
          products,
          alerts: [data as AlertMessage, ...prev.alerts].slice(0, 50),
        };
      });
    });

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      socket.disconnect();
    };
  }, [fetchInitialState]);

  return state;
}
