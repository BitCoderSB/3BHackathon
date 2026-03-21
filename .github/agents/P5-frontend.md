# Contexto para Copilot — P5: Frontend Dashboard (Módulo M9)

## Tu rol
Eres el responsable del **Dashboard interactivo en React** que consume TODA la información del sistema y la presenta en tiempo real. El dashboard es la **cara visible** del proyecto frente a los jueces — todo lo que el equipo construya se muestra aquí.

## Tu módulo

### M9 — Dashboard React
**Directorio:** `frontend/`

## Stack obligatorio
- **React 18+** con Vite
- **TailwindCSS** para estilos
- **Recharts** para gráficas
- **socket.io-client** para WebSocket en tiempo real
- **Idioma UI:** Todo en español

## Comunicación con Backend

### WebSocket (socket.io) — Eventos que escuchas
```typescript
// Conectar
const socket = io("http://localhost:8000");

// Eventos del servidor → cliente
socket.on("inventory_update", (data: InventoryState) => { ... });
socket.on("detection_event", (data: DetectionEvent) => { ... });
socket.on("video_frame", (data: { frame_base64: string }) => { ... });
socket.on("prediction_update", (data: PredictionUpdate) => { ... });
socket.on("heatmap_update", (data: HeatmapData) => { ... });
socket.on("narrative", (data: NarrativeMessage) => { ... });
socket.on("alert", (data: AlertMessage) => { ... });
```

### REST — Endpoints para consultas iniciales
```
GET  /api/inventory          → InventoryState (estado actual completo)
GET  /api/inventory/{sku_id} → ProductStock (un producto)
GET  /api/predictions        → list[StockPrediction]
GET  /api/heatmap            → HeatmapData
GET  /api/narratives         → list[NarrativeMessage] (últimas 50)
GET  /api/health             → { status: "ok", uptime: 123.4 }
```

## Tipos TypeScript

```typescript
interface ProductStock {
  sku_id: string;
  sku_name: string;
  stock_current: number;
  stock_initial: number;   // Siempre 8
  last_event: string | null; // ISO timestamp
  alert_active: boolean;
  alert_level: "normal" | "low" | "critical";
}

interface InventoryState {
  timestamp: string;
  products: ProductStock[];
  total_events: number;
}

interface DetectionEvent {
  event_id: string;
  sku_id: string;
  sku_name: string;
  action: "removed" | "returned";
  stock_before: number;
  stock_after: number;
  timestamp: string;
}

interface StockPrediction {
  sku_id: string;
  sku_name: string;
  stock_current: number;
  rate_per_hour: number;
  estimated_depletion: string | null;
  minutes_remaining: number | null;
  trend: "acelerando" | "estable" | "desacelerando";
  confidence: "alta" | "media" | "baja";
}

interface HeatmapData {
  slots: Array<{
    slot_id: number;
    sku_id: string;
    activity_count: number;
    intensity: number; // 0.0 a 1.0
  }>;
  window_seconds: number;
  last_updated: string;
}

interface NarrativeMessage {
  message_id: string;
  severity: "info" | "warning" | "critical";
  text: string;
  sku_id: string | null;
  timestamp: string;
  icon: string;
}

interface AlertMessage {
  alert_id: string;
  sku_id: string;
  sku_name: string;
  level: "low" | "critical";
  stock_current: number;
  threshold_pct: number;
  message: string;
  timestamp: string;
}
```

## Componentes del Dashboard

### Layout principal
```
┌─────────────────────────────────────────────────┐
│  🏪 Inventario en Tiempo Real — Tiendas 3B      │ ← Header
├────────────────────┬────────────────────────────┤
│                    │  📊 Panel de Stock (7 SKUs) │ ← Barras/cards
│   📹 Video Feed   │  (barras con semáforo)      │
│   (con overlay)    ├────────────────────────────┤
│                    │  🔮 Predicciones            │ ← Tabla/cards
│                    │  (tiempo restante por SKU)  │
├────────────────────┼────────────────────────────┤
│   🗺️ Heatmap      │  💬 Narrativa / Log         │
│   (actividad       │  (mensajes en scroll)       │
│    del anaquel)    │                             │
├────────────────────┴────────────────────────────┤
│  📈 Histórico de Eventos (timeline/gráfica)      │ ← Recharts
└─────────────────────────────────────────────────┘
```

### Componentes individuales

1. **StockPanel** — Barras horizontales o cards por producto
   - Color semáforo: verde (>50%), amarillo (25-50%), rojo (<25%)
   - Animación/transición cuando cambia el stock
   - Mostrar `stock_current / stock_initial`

2. **VideoFeed** — Imagen JPEG en tiempo real
   - Recibe `frame_base64` por WebSocket
   - Renderizar como `<img src="data:image/jpeg;base64,{frame}" />`
   - Indicador de FPS o "en vivo"

3. **PredictionCards** — Una card por SKU con predicción
   - Mostrar: tasa/hora, minutos restantes, tendencia (flecha ↑↓→)
   - Badge de confianza (alta/media/baja)
   - Resaltar los que van a agotarse pronto

4. **HeatmapGrid** — Representación del anaquel
   - Grid/tabla con intensidad de color por zona
   - Colores: azul frío → rojo caliente
   - Tooltip con detalles al hover

5. **NarrativeLog** — Feed de mensajes tipo chat
   - Auto-scroll hacia abajo
   - Color por severidad: gris (info), amarillo (warning), rojo (critical)
   - Mostrar icono + timestamp + texto

6. **EventTimeline** — Gráfica Recharts
   - LineChart o BarChart de eventos por minuto
   - O línea de stock por SKU a lo largo del tiempo

7. **AlertBanner** — Toast/banner superior
   - Aparece cuando llega alerta critical
   - Auto-dismiss después de 10s o click para cerrar
   - Sound/vibración opcional (nice to have)

## Mock para desarrollo sin backend
```typescript
// frontend/src/mocks/mockSocket.ts
// Simular WebSocket para trabajar sin backend

import { useEffect, useState } from "react";

const PRODUCTS = [
  { sku_id: "agua_burst", sku_name: "Agua Natural Burst 1500ml", stock_current: 7, stock_initial: 8 },
  { sku_id: "burst_energetica_roja", sku_name: "Bebida Energetica Red Burst 473ml", stock_current: 5, stock_initial: 8 },
  { sku_id: "burst_energy", sku_name: "Bebida Energetica Original Burst Energy 600ml", stock_current: 8, stock_initial: 8 },
  { sku_id: "nachos_naturasol", sku_name: "Nachos Con Sal Naturasol 200gr", stock_current: 3, stock_initial: 8 },
  { sku_id: "nebraska_mango", sku_name: "Bebida Mango-Durazno Nebraska 460ml", stock_current: 6, stock_initial: 8 },
  { sku_id: "sisi_cola", sku_name: "Refresco Cola Sin Azucar Sisi 355ml", stock_current: 8, stock_initial: 8 },
  { sku_id: "sun_paradise_naranja", sku_name: "Bebida Naranja Sun Paradise 900ml", stock_current: 4, stock_initial: 8 },
];

export function useMockInventory() {
  const [products, setProducts] = useState(PRODUCTS);
  useEffect(() => {
    const interval = setInterval(() => {
      setProducts(prev => {
        const idx = Math.floor(Math.random() * prev.length);
        const p = { ...prev[idx] };
        if (p.stock_current > 0) p.stock_current--;
        return prev.map((item, i) => i === idx ? p : item);
      });
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  return products;
}
```

## Colores TailwindCSS sugeridos
```
Verde:    bg-green-500 / text-green-700
Amarillo: bg-yellow-400 / text-yellow-700
Rojo:     bg-red-500 / text-red-700
Fondo:    bg-gray-50 / bg-gray-900 (dark mode)
Cards:    bg-white shadow-md rounded-lg p-4
Header:   bg-blue-800 text-white
```

## Los 7 productos (referencia rápida)
| sku_id | Producto |
|---|---|
| agua_burst | Agua Natural Burst 1500ml |
| burst_energetica_roja | Bebida Energetica Red Burst 473ml |
| burst_energy | Bebida Energetica Original Burst Energy 600ml |
| nachos_naturasol | Nachos Con Sal Naturasol 200gr |
| nebraska_mango | Bebida Mango-Durazno Nebraska 460ml |
| sisi_cola | Refresco Cola Sin Azucar Sisi 355ml |
| sun_paradise_naranja | Bebida Naranja Sun Paradise 900ml |

## Prioridades
1. 🔴 Layout base + StockPanel con datos mock (primero lo visual)
2. 🔴 Conexión WebSocket con socket.io-client
3. 🔴 VideoFeed mostrando frames base64
4. 🟡 NarrativeLog con auto-scroll
5. 🟡 PredictionCards
6. 🟡 EventTimeline con Recharts
7. 🟢 HeatmapGrid
8. 🟢 AlertBanner con toast
9. 🟢 Responsive / dark mode

## Si terminas antes
Ayuda con: pulir animaciones, agregar sonido en alertas, pantalla de resumen para pitch, dark mode, logo 3B, preparar demo fullscreen.
