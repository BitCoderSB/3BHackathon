# 📦 MVP — Requisitos Funcionales, Dependencias y Contratos

## Hackathon Tiendas 3B — Inventario en Tiempo Real

---

## 1. Mapa Jerárquico de Módulos (Árbol de Dependencias)

```
                        ┌─────────────────────────┐
                        │   🎥 M1: CAPTURA DE     │
                        │      VIDEO (Cámara)      │
                        │   [Sin dependencias]     │
                        └────────────┬────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │   🧠 M2: MOTOR DE       │
                        │   VISIÓN POR COMPUTADORA │
                        │   Depende de: M1         │
                        └────────────┬────────────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                ┌──────────────┐ ┌────────┐ ┌──────────────┐
                │ 📹 M5: VIDEO │ │        │ │ 🔥 M7:       │
                │ OVERLAY      │ │        │ │ HEATMAP      │
                │ Depende: M2  │ │        │ │ Depende: M2  │
                └──────┬───────┘ │        │ └──────┬───────┘
                       │         ▼        │        │
                       │  ┌─────────────┐ │        │
                       │  │ 📦 M3:      │ │        │
                       │  │ MOTOR DE    │ │        │
                       │  │ INVENTARIO  │ │        │
                       │  │ Depende: M2 │ │        │
                       │  └──────┬──────┘ │        │
                       │         │        │        │
                       │    ┌────┼────┐   │        │
                       │    ▼    │    ▼   │        │
                       │ ┌─────┐ │ ┌──────────┐   │
                       │ │ 🔮  │ │ │ 📝 M8:   │   │
                       │ │ M6: │ │ │ NARRACIÓN │   │
                       │ │PRED.│ │ │INTELIGENTE│   │
                       │ │Dep: │ │ │Dep: M3,M6│   │
                       │ │ M3  │ │ └────┬─────┘   │
                       │ └──┬──┘ │      │         │
                       │    │    ▼      │         │
                       │    │ ┌──────────────┐    │
                       │    │ │ 🔌 M4: API   │    │
                       │    │ │ BACKEND      │    │
                       │    │ │ (FastAPI +   │    │
                       │    │ │  WebSocket)  │    │
                       │    │ │ Dep: M3      │    │
                       │    │ └──────┬───────┘    │
                       │    │        │            │
                       ▼    ▼        ▼            ▼
                ┌─────────────────────────────────────┐
                │         🎨 M9: DASHBOARD            │
                │         (React + TailwindCSS)       │
                │  Depende de: M4, M5, M6, M7, M8    │
                │  (Puede arrancar con contratos/mock)│
                └─────────────────────────────────────┘
```

### Tabla de Dependencias Directas

| Módulo | Nombre | Depende de | Puede arrancar con mock? |
|---|---|---|---|
| **M1** | Captura de Video | — | N/A (es raíz) |
| **M2** | Motor de Visión (CV) | M1 | ✅ Sí, con video pregrabado |
| **M3** | Motor de Inventario | M2 | ✅ Sí, con eventos simulados |
| **M4** | API Backend | M3 | ✅ Sí, con datos hardcoded |
| **M5** | Video Overlay | M2 | ✅ Sí, con video pregrabado + detecciones fake |
| **M6** | Modelo Predictivo | M3 | ✅ Sí, con historial de eventos fake |
| **M7** | Heatmap | M2 | ✅ Sí, con coordenadas fake |
| **M8** | Narración Inteligente | M3, M6 | ✅ Sí, con estado de inventario fake |
| **M9** | Dashboard | M4, M5, M6, M7, M8 | ✅ Sí, con contratos definidos |

---

## 2. Contratos entre Módulos

Los contratos definen la **interfaz exacta** de comunicación entre módulos. Cualquier miembro del equipo puede trabajar en su módulo usando datos mock que respeten estos contratos.

---

### 📄 Contrato C1: M1 → M2 (Captura → CV)

**Tipo:** Frame de video (objeto OpenCV)

```python
# El módulo M1 entrega frames al M2 mediante un generador o callback

# Interfaz del frame
class FrameData:
    frame: np.ndarray       # Imagen BGR, shape (H, W, 3), dtype uint8
    timestamp: float         # time.time() al momento de captura
    frame_id: int            # Secuencial incremental
    resolution: tuple[int, int]  # (width, height) — esperado: (2592, 1944) o similar 5MPX

# Generador de frames (M1 expone esto)
def get_frames() -> Generator[FrameData, None, None]:
    """Yield de frames continuos desde la cámara."""
    ...
```

**Mock para M2 sin M1:**
```python
# Leer de un video pregrabado
import cv2
cap = cv2.VideoCapture("mock_video.mp4")
frame_id = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    yield FrameData(frame=frame, timestamp=time.time(), frame_id=frame_id, resolution=(frame.shape[1], frame.shape[0]))
    frame_id += 1
```

---

### 📄 Contrato C2: M2 → M3 (CV → Inventario)

**Tipo:** Evento de detección

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EventType(Enum):
    RETIRO = "retiro"        # Producto retirado del anaquel
    DEVOLUCION = "devolucion" # Producto devuelto al anaquel

@dataclass
class DetectionEvent:
    event_id: str              # UUID del evento
    event_type: EventType      # RETIRO o DEVOLUCION
    sku_id: str                # Identificador del producto (ej: "sku_001")
    sku_name: str              # Nombre legible (ej: "Coca-Cola 600ml")
    slot_id: int               # Slot del anaquel (1-7)
    confidence: float          # Confianza de la detección (0.0 - 1.0)
    timestamp: datetime        # Momento exacto del evento
    bbox: tuple[int,int,int,int]  # Bounding box (x1, y1, x2, y2) en píxeles
    count_before: int          # Conteo en slot ANTES del evento
    count_after: int           # Conteo en slot DESPUÉS del evento
```

**Mock para M3 sin M2:**
```python
mock_event = DetectionEvent(
    event_id="evt_001",
    event_type=EventType.RETIRO,
    sku_id="sku_003",
    sku_name="Galletas Marías",
    slot_id=3,
    confidence=0.92,
    timestamp=datetime.now(),
    bbox=(120, 200, 280, 350),
    count_before=5,
    count_after=4
)
```

---

### 📄 Contrato C3: M2 → M5 (CV → Video Overlay)

**Tipo:** Frame anotado con detecciones

```python
@dataclass
class AnnotatedFrame:
    frame: np.ndarray                  # Frame original BGR
    timestamp: float
    detections: list[SlotDetection]    # Detecciones activas en este frame

@dataclass
class SlotDetection:
    sku_id: str
    sku_name: str
    slot_id: int
    bbox: tuple[int, int, int, int]    # (x1, y1, x2, y2)
    confidence: float
    count: int                          # Cantidad actual detectada en el slot
    stock_level: str                    # "ok" | "warning" | "critical"
```

---

### 📄 Contrato C4: M2 → M7 (CV → Heatmap)

**Tipo:** Evento de interacción por zona

```python
@dataclass
class InteractionEvent:
    slot_id: int                        # Slot donde ocurrió la interacción
    sku_id: str
    region: tuple[int, int, int, int]   # Región del anaquel (x1, y1, x2, y2)
    timestamp: datetime
    interaction_type: str               # "hand_detected" | "product_moved"
```

---

### 📄 Contrato C5: M3 → M4 (Inventario → API)

**Tipo:** Estado de inventario + Eventos

```python
# Estado completo del inventario (M3 expone este objeto)
@dataclass
class InventoryState:
    last_updated: datetime
    products: list[ProductStock]

@dataclass
class ProductStock:
    sku_id: str
    sku_name: str
    slot_id: int
    stock_initial: int          # Stock con el que se inició
    stock_current: int          # Stock actual
    stock_min_threshold: float  # Umbral de alerta (default 0.20 = 20%)
    is_alert: bool              # True si stock_current <= stock_initial * threshold
    last_event: datetime | None

# Evento para historial (M3 registra y M4 expone)
@dataclass
class InventoryEvent:
    event_id: str
    event_type: str             # "retiro" | "devolucion"
    sku_id: str
    sku_name: str
    slot_id: int
    stock_before: int
    stock_after: int
    confidence: float
    timestamp: datetime
```

---

### 📄 Contrato C6: M3 → M6 (Inventario → Predicción)

**Tipo:** Historial de eventos por SKU

```python
# M6 consume el historial de retiros para calcular predicciones
@dataclass
class SKUHistory:
    sku_id: str
    sku_name: str
    stock_current: int
    stock_initial: int
    events: list[datetime]      # Lista de timestamps de cada retiro

# M6 produce predicciones
@dataclass
class StockPrediction:
    sku_id: str
    sku_name: str
    stock_current: int
    rate_per_hour: float        # Tasa de retiro (unidades/hora)
    estimated_depletion: datetime | None  # Hora estimada de agotamiento
    minutes_remaining: float | None       # Minutos estimados hasta agotamiento
    trend: str                  # "acelerando" | "estable" | "desacelerando"
    confidence: str             # "alta" | "media" | "baja" (basado en cantidad de datos)
```

---

### 📄 Contrato C7: M3 + M6 → M8 (Inventario + Predicción → Narración)

**Tipo:** Datos combinados para generar narrativa

```python
# M8 recibe estado de inventario y predicciones
@dataclass
class NarrativeInput:
    inventory: InventoryState
    predictions: list[StockPrediction]
    recent_events: list[InventoryEvent]  # Últimos N eventos

# M8 produce mensajes narrativos
@dataclass
class NarrativeMessage:
    message_id: str
    severity: str               # "info" | "warning" | "critical"
    text: str                   # Texto legible para humanos
    sku_id: str | None          # SKU relacionado (o None si es general)
    timestamp: datetime
    icon: str                   # Emoji sugerido para el frontend
```

---

### 📄 Contrato C8: M4 → M9 (API → Dashboard)

**Tipo:** Endpoints REST + WebSocket

#### Endpoints REST

```
GET  /api/inventory
     → Response: InventoryState (JSON)

GET  /api/inventory/{sku_id}
     → Response: ProductStock (JSON)

GET  /api/events?limit=50&sku_id=optional
     → Response: list[InventoryEvent] (JSON)

GET  /api/predictions
     → Response: list[StockPrediction] (JSON)

GET  /api/heatmap
     → Response: HeatmapData (JSON)

GET  /api/narratives?limit=10
     → Response: list[NarrativeMessage] (JSON)

POST /api/inventory/reset
     → Reinicia inventario a valores iniciales (para demo)

PUT  /api/config/threshold
     → Body: { "threshold": 0.20 }
     → Actualiza umbral de alerta
```

#### WebSocket

```
WS   /ws/live

# Mensajes del servidor → cliente (JSON):

# Actualización de inventario
{
    "type": "inventory_update",
    "data": {
        "sku_id": "sku_003",
        "sku_name": "Galletas Marías",
        "slot_id": 3,
        "stock_before": 5,
        "stock_after": 4,
        "event_type": "retiro",
        "confidence": 0.92,
        "timestamp": "2026-03-21T14:32:01Z"
    }
}

# Alerta de umbral
{
    "type": "alert",
    "data": {
        "sku_id": "sku_003",
        "sku_name": "Galletas Marías",
        "stock_current": 2,
        "stock_initial": 8,
        "percentage": 0.25,
        "threshold": 0.20,
        "message": "Stock bajo — próximo a alcanzar umbral"
    }
}

# Predicción actualizada
{
    "type": "prediction_update",
    "data": {
        "sku_id": "sku_003",
        "minutes_remaining": 20.5,
        "rate_per_hour": 5.8,
        "trend": "acelerando"
    }
}

# Narrativa nueva
{
    "type": "narrative",
    "data": {
        "severity": "warning",
        "text": "⚠️ Galletas Marías ha tenido 3 retiros en 5 min...",
        "sku_id": "sku_003",
        "icon": "⚠️"
    }
}

# Heatmap update
{
    "type": "heatmap_update",
    "data": {
        "slots": [
            {"slot_id": 1, "activity_count": 2, "intensity": 0.25},
            {"slot_id": 2, "activity_count": 5, "intensity": 0.63},
            {"slot_id": 3, "activity_count": 8, "intensity": 1.00}
        ]
    }
}

# Frame de video (stream alternativo)
{
    "type": "video_frame",
    "data": {
        "frame_base64": "...",   # JPEG codificado en base64
        "detections_overlay": true,
        "timestamp": "2026-03-21T14:32:01Z"
    }
}
```

**Mock para M9 sin backend real:**
```javascript
// mock-websocket.js — Simula mensajes del backend
const mockInventory = {
  last_updated: new Date().toISOString(),
  products: [
    { sku_id: "sku_001", sku_name: "Coca-Cola 600ml", slot_id: 1, stock_initial: 8, stock_current: 8, is_alert: false },
    { sku_id: "sku_002", sku_name: "Sabritas Original", slot_id: 2, stock_initial: 8, stock_current: 6, is_alert: false },
    { sku_id: "sku_003", sku_name: "Galletas Marías", slot_id: 3, stock_initial: 8, stock_current: 2, is_alert: true },
    { sku_id: "sku_004", sku_name: "Agua Ciel 1L", slot_id: 4, stock_initial: 8, stock_current: 7, is_alert: false },
    { sku_id: "sku_005", sku_name: "Jabón Zote", slot_id: 5, stock_initial: 8, stock_current: 5, is_alert: false },
    { sku_id: "sku_006", sku_name: "Frijoles La Costeña", slot_id: 6, stock_initial: 8, stock_current: 8, is_alert: false },
    { sku_id: "sku_007", sku_name: "Papel Higiénico Pétalo", slot_id: 7, stock_initial: 8, stock_current: 4, is_alert: false },
  ]
};

// Emitir evento simulado cada 5 segundos
setInterval(() => {
  const randomSku = mockInventory.products[Math.floor(Math.random() * 7)];
  if (randomSku.stock_current > 0) {
    randomSku.stock_current--;
    const event = {
      type: "inventory_update",
      data: {
        sku_id: randomSku.sku_id,
        sku_name: randomSku.sku_name,
        slot_id: randomSku.slot_id,
        stock_before: randomSku.stock_current + 1,
        stock_after: randomSku.stock_current,
        event_type: "retiro",
        confidence: 0.85 + Math.random() * 0.15,
        timestamp: new Date().toISOString()
      }
    };
    // ws.send(JSON.stringify(event));
    console.log("Mock event:", event);
  }
}, 5000);
```

---

## 3. Requisitos Funcionales por Módulo

---

### 🎥 M1: Captura de Video

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M1-RF01 | Conectarse a cámara USB o IP | CRÍTICO | Stream de video estable a ≥10 FPS |
| M1-RF02 | Entregar frames como `np.ndarray` BGR | CRÍTICO | Shape (H, W, 3), dtype uint8 |
| M1-RF03 | Incluir timestamp y frame_id por frame | ALTO | Precisión de milisegundos |
| M1-RF04 | Soportar resolución configurable | MEDIO | Parámetro en config, default 1280x720 |
| M1-RF05 | Reconectar automáticamente si la cámara se desconecta | MEDIO | Reintentar cada 2s, máximo 10 intentos |
| M1-RF06 | Soportar video pregrabado como fuente alternativa | ALTO | Para testing y desarrollo sin cámara |

**Entregable:** Generador de frames que abstrae la fuente (cámara real o video).

---

### 🧠 M2: Motor de Visión por Computadora

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M2-RF01 | Detectar los 7 SKUs por empaque visual | CRÍTICO | mAP ≥ 0.80 sobre dataset de validación |
| M2-RF02 | Contar instancias por slot en cada frame | CRÍTICO | Conteo correcto ±0 en condiciones normales |
| M2-RF03 | Generar `DetectionEvent` al detectar cambio de conteo | CRÍTICO | Evento emitido en < 2 segundos desde el retiro |
| M2-RF04 | Detectar RETIRO (decremento) | CRÍTICO | Conteo baja → emitir evento tipo RETIRO |
| M2-RF05 | Detectar DEVOLUCIÓN (incremento) | ALTO | Conteo sube → emitir evento tipo DEVOLUCION |
| M2-RF06 | Implementar cooldown anti-duplicados por slot | CRÍTICO | No emitir 2 eventos del mismo slot en < N seg (configurable, default 3s) |
| M2-RF07 | Doble validación: comparar snapshots pre/post interacción | ALTO | Solo emitir si la diferencia persiste en ≥3 frames consecutivos |
| M2-RF08 | Opcionalmente detectar presencia de mano como trigger | MEDIO | Usar MediaPipe o modelo secundario |
| M2-RF09 | Umbral de confianza configurable | ALTO | Default 0.70, ajustable sin reiniciar |
| M2-RF10 | Warm-up del modelo al iniciar | ALTO | Ejecutar 3 inferences dummy antes de procesar video real |
| M2-RF11 | Entregar `AnnotatedFrame` al módulo de overlay | ALTO | Frame + lista de detecciones con bbox |
| M2-RF12 | Entregar `InteractionEvent` al módulo de heatmap | MEDIO | Coordenadas de zona interactuada |

**Entregable:** Pipeline de detección que consume frames y produce eventos + frames anotados.

---

### 📦 M3: Motor de Inventario

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M3-RF01 | Mantener estado de inventario por SKU (7 productos) | CRÍTICO | Estructura en memoria con persistencia opcional |
| M3-RF02 | Procesar `DetectionEvent` y actualizar stock | CRÍTICO | Stock actualizado en < 100ms desde recibir evento |
| M3-RF03 | Decrementar exactamente 1 unidad por evento RETIRO | CRÍTICO | Nunca decrementar más de 1, nunca bajar de 0 |
| M3-RF04 | Incrementar 1 unidad por evento DEVOLUCION | ALTO | Nunca exceder stock_initial |
| M3-RF05 | Calcular y emitir alerta cuando stock ≤ umbral | CRÍTICO | Umbral default 20%, configurable |
| M3-RF06 | Registrar historial de todos los eventos con timestamp | ALTO | Persistir en lista/BD para consulta posterior |
| M3-RF07 | Exponer estado actual via método síncrono | ALTO | `get_inventory_state() → InventoryState` |
| M3-RF08 | Exponer historial de eventos por SKU | ALTO | `get_sku_history(sku_id) → SKUHistory` |
| M3-RF09 | Soportar reset de inventario | MEDIO | Volver a stock_initial para todos los SKUs |
| M3-RF10 | Ignorar eventos con confianza menor al umbral | ALTO | No procesar si `confidence < threshold` |
| M3-RF11 | Notificar cambios via callback/event bus | ALTO | Observer pattern para que M4, M6, M8 reaccionen |

**Entregable:** Clase `InventoryEngine` con estado, historial y notificaciones.

---

### 🔌 M4: API Backend (FastAPI + WebSocket)

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M4-RF01 | `GET /api/inventory` — Estado completo | CRÍTICO | JSON con todos los SKUs y stock actual |
| M4-RF02 | `GET /api/events` — Historial de eventos | ALTO | Paginado, filtrable por sku_id |
| M4-RF03 | `GET /api/predictions` — Predicciones activas | ALTO | JSON con predicción por SKU |
| M4-RF04 | `GET /api/heatmap` — Datos del heatmap | MEDIO | JSON con intensidad por slot |
| M4-RF05 | `GET /api/narratives` — Últimas narrativas | MEDIO | JSON con mensajes recientes |
| M4-RF06 | `POST /api/inventory/reset` — Reset de inventario | MEDIO | Volver a estado inicial |
| M4-RF07 | `PUT /api/config/threshold` — Actualizar umbral | MEDIO | Cambiar umbral dinámicamente |
| M4-RF08 | `WS /ws/live` — Stream en tiempo real | CRÍTICO | Push de inventory_update, alert, prediction_update, narrative, heatmap_update |
| M4-RF09 | `WS /ws/video` o endpoint MJPEG — Stream de video | ALTO | Frames con overlay a ≥5 FPS |
| M4-RF10 | CORS habilitado para frontend local | ALTO | Permitir localhost:5173 (Vite default) |
| M4-RF11 | Manejo de múltiples clientes WebSocket | MEDIO | Broadcast a todos los clientes conectados |

**Entregable:** Servidor FastAPI con todos los endpoints + WebSocket funcional.

---

### 📹 M5: Video Overlay Aumentado

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M5-RF01 | Dibujar bounding boxes sobre productos detectados | ALTO | Rectángulos con color según stock_level |
| M5-RF02 | Mostrar etiqueta con nombre de SKU y conteo | ALTO | Texto legible sobre cada bbox |
| M5-RF03 | Color semáforo: verde (ok), amarillo (warning), rojo (critical) | ALTO | Verde >50%, Amarillo 20-50%, Rojo ≤20% |
| M5-RF04 | Animación de "flash" al detectar retiro/devolución | MEDIO | Parpadeo breve en el slot afectado |
| M5-RF05 | Codificar frame anotado como JPEG/base64 para transmisión | ALTO | Calidad 70-85% para balance rendimiento/calidad |
| M5-RF06 | Mantener ≥5 FPS en el stream de video | ALTO | No bloquear pipeline principal |

**Entregable:** Función que transforma `AnnotatedFrame` en frame con overlay visual listo para transmitir.

---

### 🔮 M6: Modelo Predictivo de Desabasto

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M6-RF01 | Calcular tasa de retiro por SKU (unidades/hora) | ALTO | Ventana deslizante de últimos N eventos o T minutos |
| M6-RF02 | Predecir tiempo estimado de agotamiento | ALTO | `minutos_remaining = tasa * stock_actual` |
| M6-RF03 | Usar suavizado exponencial (α configurable) | ALTO | Más peso a eventos recientes |
| M6-RF04 | Calcular tendencia: acelerando / estable / desacelerando | MEDIO | Comparar tasa ventana reciente vs ventana anterior |
| M6-RF05 | Indicar nivel de confianza de la predicción | MEDIO | Baja (<3 eventos), Media (3-6), Alta (>6) |
| M6-RF06 | Actualizar predicción tras cada nuevo evento | ALTO | Recalcular en < 50ms |
| M6-RF07 | Manejar caso sin datos suficientes | ALTO | Retornar None, no inventar predicciones |
| M6-RF08 | Exponer predicciones como `list[StockPrediction]` | ALTO | Consumible por M4 (API) y M8 (narración) |

**Entregable:** Clase `PredictionEngine` que consume historial y produce predicciones por SKU.

---

### 🔥 M7: Heatmap de Actividad

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M7-RF01 | Acumular interacciones por slot del anaquel | MEDIO | Contador incremental por slot |
| M7-RF02 | Calcular intensidad relativa (0.0 a 1.0) | MEDIO | Normalizado: slot más activo = 1.0 |
| M7-RF03 | Soportar ventana temporal configurable | BAJO | Últimos N minutos o "desde inicio" |
| M7-RF04 | Generar datos para visualización tipo heatmap | MEDIO | JSON con slot_id + intensity |
| M7-RF05 | Actualizar cada N segundos (configurable, default 10s) | BAJO | No saturar el frontend |

**Entregable:** Clase `HeatmapEngine` que acumula interacciones y expone datos heatmap.

---

### 📝 M8: Narración Inteligente

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M8-RF01 | Generar mensaje al detectar retiro | ALTO | Template: "SKU_NAME retirado del slot N. Stock: X" |
| M8-RF02 | Generar alerta al alcanzar umbral | CRÍTICO | Template: "⚠️ SKU_NAME alcanzó umbral crítico (X%)" |
| M8-RF03 | Generar mensaje predictivo | ALTO | Template: "SKU_NAME se agotará en ~N min al ritmo actual" |
| M8-RF04 | Generar resumen de estado general | MEDIO | "Todos los productos OK" o "N productos en alerta" |
| M8-RF05 | Generar mensaje de devolución | MEDIO | Template: "SKU_NAME devuelto. Stock ajustado: X → Y" |
| M8-RF06 | Asignar severidad (info/warning/critical) e icono | ALTO | Basado en reglas de negocio |
| M8-RF07 | Limitar frecuencia de mensajes similares | MEDIO | No repetir misma narrativa en <30 segundos |
| M8-RF08 | Exponer como `list[NarrativeMessage]` | ALTO | Últimos N mensajes, más reciente primero |

**Entregable:** Clase `NarrativeEngine` que genera mensajes legibles a partir de eventos e inventario.

---

### 🎨 M9: Dashboard (React)

| ID | Requisito | Prioridad | Criterio de Aceptación |
|---|---|---|---|
| M9-RF01 | Mostrar stock actual por SKU con barras/indicadores | CRÍTICO | 7 productos visibles con cantidad numérica |
| M9-RF02 | Colores semáforo en indicadores de stock | CRÍTICO | Verde / Amarillo / Rojo según nivel |
| M9-RF03 | Actualización en tiempo real (sin recargar) | CRÍTICO | WebSocket conectado, UI reactiva |
| M9-RF04 | Alerta visual al alcanzar umbral | CRÍTICO | Toast, banner o animación prominente |
| M9-RF05 | Feed de video en vivo con overlay | ALTO | Cuadro de video con bounding boxes |
| M9-RF06 | Log de eventos en tiempo real | ALTO | Lista scrollable con eventos recientes |
| M9-RF07 | Panel de predicciones (tiempo estimado de agotamiento) | ALTO | Por SKU, con indicador de tendencia |
| M9-RF08 | Heatmap visual del anaquel | MEDIO | Representación gráfica con gradiente de colores |
| M9-RF09 | Sección de narración inteligente | ALTO | Mensajes textuales con severidad e ícono |
| M9-RF10 | Gráfica temporal de evolución de stock | MEDIO | Líneas por SKU, eje X = tiempo |
| M9-RF11 | Configuración de umbral de alerta | MEDIO | Input numérico que hace PUT a la API |
| M9-RF12 | Botón de reset de inventario | MEDIO | POST a /api/inventory/reset + confirmación |
| M9-RF13 | Vista operativa (empleado) y vista analítica (gerente) | BAJO | Tab o toggle para cambiar entre vistas |
| M9-RF14 | Responsive y usable en pantalla de 1080p | ALTO | Sin scroll horizontal, información visible |
| M9-RF15 | Sonido opcional al emitir alerta | BAJO | Beep corto al alcanzar umbral |

**Entregable:** SPA en React con todas las vistas y conexión WebSocket al backend.

---

## 4. Flujo de Datos End-to-End

```
CÁMARA ──frame──▶ M1 ──FrameData──▶ M2 ──┬── DetectionEvent ──▶ M3 ──┬── InventoryState ──▶ M4 ──┬── REST/WS ──▶ M9
                                          │                           │                           │
                                          ├── AnnotatedFrame ──▶ M5 ──┤── video stream ──────────▶│
                                          │                           │                           │
                                          └── InteractionEvent ──▶ M7 ┤── heatmap data ─────────▶│
                                                                      │                           │
                                                                      ├── SKUHistory ──▶ M6 ──┬──▶│
                                                                      │                       │   │
                                                                      └── InventoryState+M6 ──▶ M8──▶│
```

---

## 5. 📂 Assets del Hackathon — Mapeo y Uso Correcto

### 5.1 Estructura real de assets

```
assets/
├── cadenadeconexion.md                          ← URLs RTSP de cámaras + credenciales
├── Hackaton-datos_productos.csv                 ← 14 productos (superset, incluye los del anaquel)
├── productosdelanaquel.md                       ← 7 productos JSON (los que están EN el anaquel)
└── project-7-at-2026-03-20-21-09-0e2e8304/      ← Dataset etiquetado (Label Studio export)
    ├── classes.txt                              ← 7 clases YOLO (nombres del modelo)
    ├── notes.json                               ← Metadata de categorías (COCO-style)
    ├── images/                                  ← 71 imágenes JPG del anaquel (2 cámaras)
    └── labels/                                  ← 71 archivos TXT con anotaciones
```

### 5.2 ⚠️ Hallazgos Críticos del Dataset

| Hallazgo | Detalle | Impacto |
|---|---|---|
| **Formato de labels** | YOLO **POLYGON** (segmentación), NO bbox estándar | Usar `yolo task=segment` o convertir a bbox |
| **Cantidad de imágenes** | 71 imágenes | Suficiente para fine-tuning, se recomienda **data augmentation** |
| **Fuentes de imagen** | 2 cámaras (`camara_1`, `camara_2`) | El modelo debe generalizar entre ambas |
| **Herramienta de etiquetado** | Label Studio | Export compatible con YOLO |
| **7 clases** | Coinciden exactamente con los 7 productos del anaquel | Mapeo 1:1 validado |

#### Formato de labels (YOLO-Seg Polygon):
```
# Cada línea: class_id x1 y1 x2 y2 x3 y3 ... (coordenadas normalizadas del polígono)
# Ejemplo: clase 1 (burst_energetica_roja) con polígono de 18 puntos
1 0.5134 0.1556 0.5136 0.1504 0.5168 0.1500 ...
```

**Opciones para el entrenamiento:**
1. **Usar YOLOv8-seg** (segmentación de instancias) → usa polígonos directamente ✅ **RECOMENDADO**
2. **Convertir a bbox** → extraer min/max de cada polígono → formato YOLO estándar (class cx cy w h)

### 5.3 Cámaras RTSP (Conexión Real)

```python
RTSP_CAMARAS = [
    "rtsp://admin:admin1234@172.31.13.190:554/cam/realmonitor?channel=1&subtype=0",
    "rtsp://admin:admin1234@172.31.13.191:554/cam/realmonitor?channel=1&subtype=0"
]
# Credenciales: admin / admin1234
# Las cámaras simulan entorno real de tienda
# Se permite mock de video si no se puede consumir RTSP en vivo
```

### 5.4 Mapeo Clase YOLO ↔ Producto Real ↔ CSV

| Class ID | Clase YOLO | Producto (JSON anaquel) | src_product_id (CSV) | barcode |
|---|---|---|---|---|
| 0 | `agua_burst` | Agua Natural Burst 1500ml | 7746 | 7502261250185 |
| 1 | `burst_energetica_roja` | Bebida Energetica Red Burst 473ml | 11024 | 7502261254411 |
| 2 | `burst_energy` | Bebida Energetica Original Burst Energy 600ml | 22013 | 7502261273047 |
| 3 | `nachos_naturasol` | Nachos Con Sal Naturasol 200gr | 25996 | 7503052023278 |
| 4 | `nebraska_mango` | Bebida Mango-Durazno Nebraska 460ml | 26449 | 7502261273504 |
| 5 | `sisi_cola` | Refresco Cola Sin Azucar Sisi 355ml | 22287 | 7502261272415 |
| 6 | `sun_paradise_naranja` | Bebida Naranja Sun Paradise 900ml | 24338 | 7502261269576 |

### 5.5 ¿Quién usa qué asset?

| Asset | Módulo(s) | Persona | Uso |
|---|---|---|---|
| `project-7-.../images/` + `labels/` | M2 (CV) | **P1** | Entrenamiento y validación del modelo YOLO |
| `project-7-.../classes.txt` | M2, M3 | **P1, P3** | Nombres de clases para el modelo y mapeo de inventario |
| `productosdelanaquel.md` (JSON) | M3, M4, M9 | **P3, P5** | Catálogo de productos con metadata (nombre, barcode, precio) |
| `Hackaton-datos_productos.csv` | M3, M4 | **P3** | Datos extendidos de productos (puede servir como BD semilla) |
| `cadenadeconexion.md` (RTSP) | M1 | **P2** | Conexión a cámaras reales para demo en vivo |

---

## 6. Configuración Global (Compartida)

```python
# config.py — Configuración central del sistema
CONFIG = {
    # Cámara (RTSP real del hackathon)
    "camera_source": "rtsp://admin:admin1234@172.31.13.190:554/cam/realmonitor?channel=1&subtype=0",
    "camera_source_alt": "rtsp://admin:admin1234@172.31.13.191:554/cam/realmonitor?channel=1&subtype=0",
    "camera_fallback": 0,                # USB local como fallback
    "camera_resolution": (1280, 720),
    "camera_fps_target": 15,

    # Modelo CV (entrenado con dataset del hackathon)
    "model_path": "models/best.pt",      # Modelo YOLOv8-seg entrenado
    "model_task": "segment",             # Segmentación (polígonos) — el dataset lo soporta
    "confidence_threshold": 0.70,
    "cooldown_seconds": 3.0,
    "validation_frames": 3,              # Frames consecutivos para confirmar cambio

    # Dataset (assets del hackathon)
    "dataset_path": "assets/project-7-at-2026-03-20-21-09-0e2e8304",
    "classes_file": "assets/project-7-at-2026-03-20-21-09-0e2e8304/classes.txt",
    "products_json": "assets/productosdelanaquel.md",  # JSON embebido en .md
    "products_csv": "assets/Hackaton-datos_productos.csv",

    # Inventario
    "stock_initial": 8,                  # Unidades iniciales por SKU
    "alert_threshold": 0.20,             # 20% del stock inicial

    # Predicción
    "prediction_alpha": 0.3,             # Suavizado exponencial
    "prediction_min_events": 2,          # Mínimo de eventos para predecir

    # Heatmap
    "heatmap_window_seconds": 300,       # Ventana de 5 minutos
    "heatmap_update_interval": 10,       # Actualizar cada 10s

    # Narración
    "narrative_cooldown_seconds": 30,    # No repetir mismo tipo de mensaje en 30s
    "narrative_max_messages": 50,        # Retener últimas 50 narrativas

    # API
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "cors_origins": ["http://localhost:5173", "http://localhost:3000"],

    # Video Overlay
    "overlay_jpeg_quality": 80,
    "overlay_target_fps": 10,

    # SKUs registrados (DATOS REALES del hackathon)
    "skus": [
        {"sku_id": "agua_burst",            "class_id": 0, "name": "Agua Natural Burst 1500ml",              "product_id": 7746,  "barcode": "7502261250185", "slot_id": 1},
        {"sku_id": "burst_energetica_roja", "class_id": 1, "name": "Bebida Energetica Red Burst 473ml",       "product_id": 11024, "barcode": "7502261254411", "slot_id": 2},
        {"sku_id": "burst_energy",          "class_id": 2, "name": "Bebida Energetica Original Burst 600ml", "product_id": 22013, "barcode": "7502261273047", "slot_id": 3},
        {"sku_id": "nachos_naturasol",      "class_id": 3, "name": "Nachos Con Sal Naturasol 200gr",          "product_id": 25996, "barcode": "7503052023278", "slot_id": 4},
        {"sku_id": "nebraska_mango",        "class_id": 4, "name": "Bebida Mango-Durazno Nebraska 460ml",     "product_id": 26449, "barcode": "7502261273504", "slot_id": 5},
        {"sku_id": "sisi_cola",             "class_id": 5, "name": "Refresco Cola Sin Azucar Sisi 355ml",     "product_id": 22287, "barcode": "7502261272415", "slot_id": 6},
        {"sku_id": "sun_paradise_naranja",  "class_id": 6, "name": "Bebida Naranja Sun Paradise 900ml",       "product_id": 24338, "barcode": "7502261269576", "slot_id": 7},
    ]
}
```

---

## 7. Estrategia de Trabajo Paralelo (5 Personas)

Gracias a los contratos definidos, **5 personas** pueden trabajar en paralelo desde el minuto 0:

| Persona | Rol Inicial | Módulos Principales | Puede arrancar ya? | Necesita mock de |
|---|---|---|---|---|
| **P1 — CV/IA Lead** | Entrenar modelo YOLO + pipeline de detección | M2 (core) | ✅ Sí | Video pregrabado o imágenes del dataset |
| **P2 — CV/Cámara** | Captura de video + overlay + integración cámara RTSP | M1, M5 | ✅ Sí | Detecciones fake para overlay |
| **P3 — Backend Core** | Motor inventario + API REST + WebSocket | M3, M4 | ✅ Sí | Eventos simulados (sin M2) |
| **P4 — Backend Inteligencia** | Predicción + Heatmap + Narración | M6, M7, M8 | ✅ Sí | Historial de eventos fake |
| **P5 — Frontend** | Dashboard completo React | M9 | ✅ Sí | Mock WebSocket + datos fake |

### Reasignación dinámica

Cuando una persona termina su módulo, puede tomar cualquier tarea disponible:

```
┌─────────────────────────────────────────────────────────────────┐
│  POOL DE TAREAS DISPONIBLES (por prioridad)                     │
├─────────────────────────────────────────────────────────────────┤
│  🔴 CRÍTICO  → Ayudar en integración CV↔Backend                │
│  🔴 CRÍTICO  → Testing end-to-end / bugs                       │
│  🟡 ALTO     → Mejorar UI del dashboard                        │
│  🟡 ALTO     → Data augmentation para mejorar modelo           │
│  🟢 MEDIO    → Preparar pitch y slides                         │
│  🟢 MEDIO    → Agregar sonido/animaciones al dashboard          │
│  🔵 BAJO     → Documentación / README                          │
└─────────────────────────────────────────────────────────────────┘
```

### Orden de integración sugerido (5 personas):

```
Hora 0-3:    TRABAJO PARALELO CON MOCKS (todos simultáneamente)
             P1: Prepara dataset YOLO → entrena modelo → valida mAP
             P2: Captura RTSP/USB + módulo overlay con detecciones fake
             P3: Motor inventario + API REST + WebSocket server
             P4: Engines de predicción + heatmap + narración (con eventos mock)
             P5: Dashboard completo con mock WebSocket y datos fake

Hora 3-4:    INTEGRACIÓN FASE 1
             P1+P2: Integrar M1+M2 (cámara real → modelo CV)
             P3+P4: Integrar M3 con M6,M7,M8 (inventario → inteligencia)
             P5: Pulir UI + preparar conexión real con backend

Hora 4-5:    INTEGRACIÓN FASE 2
             P1+P3: Conectar CV → Inventario → API (M2→M3→M4)
             P2+P5: Conectar video overlay + dashboard (M5→M9)
             P4: Validar predicciones y narrativas con datos reales

Hora 5-6:    INTEGRACIÓN FINAL
             TODOS: End-to-end completo → cámara a dashboard
             Ajustar umbrales, cooldowns, confianza

Hora 6-7:    TESTING + POLISH
             P1+P2: Ajustar modelo (confianza, falsos positivos)
             P3+P4: Estabilidad backend, edge cases
             P5: UX final, animaciones, alertas

Hora 7-8:    DEMO + PITCH
             TODOS: Ensayo de demo en vivo
             Preparar pitch, plan B, warm-up del modelo
```

---

## 8. Catálogo de SKUs (Datos Reales del Hackathon)

| YOLO Class ID | Clase (modelo) | Producto Real | Presentación | Barcode | Tipo | Línea | Grupo | iVenta | Slot | Stock Inicial | Umbral 20% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `agua_burst` | Agua Natural Burst | 1500 ml | 7502261250185 | MP | Agua Natural | Water | 6 | 1 | 8 | ≤ 1 |
| 1 | `burst_energetica_roja` | Bebida Energetica Red Burst | 473 ml | 7502261254411 | MP | Energetica Isotonica | Beverages | 1 | 2 | 8 | ≤ 1 |
| 2 | `burst_energy` | Bebida Energetica Original Burst Energy | 600 ml | 7502261273047 | MP | Energetica Isotonica | Beverages | 12.5 | 3 | 8 | ≤ 1 |
| 3 | `nachos_naturasol` | Nachos Con Sal Naturasol | 200 gr | 7503052023278 | MC | Frituras | Snacks | 22 | 4 | 8 | ≤ 1 |
| 4 | `nebraska_mango` | Bebida Mango-Durazno Nebraska | 460 ml | 7502261273504 | MP | Jugos y Bebidas | Beverages | 14 | 5 | 8 | ≤ 1 |
| 5 | `sisi_cola` | Refresco Cola Sin Azucar Sisi | 355 ml | 7502261272415 | MP | Refrescos | Beverages | 11 | 6 | 8 | ≤ 1 |
| 6 | `sun_paradise_naranja` | Bebida Naranja Sun Paradise | 900 ml | 7502261269576 | MP | Jugos y Bebidas | Beverages | 18 | 7 | 8 | ≤ 1 |

> **Fuente:** `assets/productosdelanaquel.md` (JSON) y `assets/Hackaton-datos_productos.csv`. Las clases YOLO provienen de `assets/project-7-at-2026-03-20-21-09-0e2e8304/classes.txt`.

---

## 9. Checklist de Integración

- [ ] M1 entrega frames a M2 correctamente
- [ ] M2 genera `DetectionEvent` que M3 procesa
- [ ] M2 genera `AnnotatedFrame` que M5 renderiza
- [ ] M2 genera `InteractionEvent` que M7 acumula
- [ ] M3 actualiza inventario y notifica a M4
- [ ] M3 entrega historial a M6 para predicción
- [ ] M6 produce `StockPrediction` expuesta por M4
- [ ] M3 + M6 alimentan M8 para narrativas
- [ ] M4 expone REST + WebSocket funcional
- [ ] M9 consume WebSocket y renderiza todo en tiempo real
- [ ] M9 muestra video con overlay (M5)
- [ ] M9 muestra heatmap (M7)
- [ ] M9 muestra predicciones (M6)
- [ ] M9 muestra narrativas (M8)
- [ ] Alerta visual funciona al cruzar umbral
- [ ] Reset de inventario funciona desde dashboard
- [ ] Demo end-to-end estable por ≥5 minutos

---

> **Regla de oro:** Si un módulo no está listo, el que depende de él debe funcionar con el mock definido en su contrato. Nadie espera a nadie.
