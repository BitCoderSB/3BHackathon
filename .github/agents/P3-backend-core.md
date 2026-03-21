# Contexto para Copilot — P3: Backend Core (Módulos M3 + M4)

## Tu rol
Eres el responsable del **motor de inventario** y la **API backend**. Tu trabajo es recibir eventos de detección del módulo CV, mantener el estado del inventario, y exponer todo vía REST + WebSocket para que el dashboard lo consuma.

## Tus módulos

### M3 — Motor de Inventario
**Archivo:** `backend/inventory_engine.py`

#### Input que recibes de M2 (Contrato C2)
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EventType(Enum):
    RETIRO = "retiro"
    DEVOLUCION = "devolucion"

@dataclass
class DetectionEvent:
    event_id: str
    event_type: EventType
    sku_id: str               # ej: "agua_burst"
    sku_name: str             # ej: "Agua Natural Burst 1500ml"
    slot_id: int              # 1-7
    confidence: float         # 0.0-1.0
    timestamp: datetime
    bbox: tuple[int,int,int,int]
    count_before: int
    count_after: int
```

#### Output que produces (Contrato C5)
```python
@dataclass
class ProductStock:
    sku_id: str
    sku_name: str
    slot_id: int
    stock_initial: int        # 8
    stock_current: int        # Estado actual
    stock_min_threshold: float  # 0.20
    is_alert: bool
    last_event: datetime | None

@dataclass
class InventoryState:
    last_updated: datetime
    products: list[ProductStock]

@dataclass
class InventoryEvent:
    event_id: str
    event_type: str           # "retiro" | "devolucion"
    sku_id: str
    sku_name: str
    slot_id: int
    stock_before: int
    stock_after: int
    confidence: float
    timestamp: datetime
```

#### Output para M6 — Predicción (Contrato C6)
```python
@dataclass
class SKUHistory:
    sku_id: str
    sku_name: str
    stock_current: int
    stock_initial: int
    events: list[datetime]  # Timestamps de cada retiro
```

#### Lógica de negocio
- **Decrementar exactamente 1** por evento RETIRO (nunca bajar de 0)
- **Incrementar exactamente 1** por evento DEVOLUCION (nunca exceder stock_initial)
- **Alerta** cuando `stock_current <= stock_initial * threshold` (default 20%)
- **Ignorar** eventos con `confidence < confidence_threshold`
- **Notificar** cambios vía callback/observer para que M4, M6, M8 reaccionen
- **Reset:** Método para volver a stock_initial (para demo)

#### Los 7 productos (datos reales)
```python
PRODUCTOS = [
    {"sku_id": "agua_burst",            "class_id": 0, "name": "Agua Natural Burst 1500ml",              "slot_id": 1},
    {"sku_id": "burst_energetica_roja", "class_id": 1, "name": "Bebida Energetica Red Burst 473ml",       "slot_id": 2},
    {"sku_id": "burst_energy",          "class_id": 2, "name": "Bebida Energetica Original Burst 600ml", "slot_id": 3},
    {"sku_id": "nachos_naturasol",      "class_id": 3, "name": "Nachos Con Sal Naturasol 200gr",          "slot_id": 4},
    {"sku_id": "nebraska_mango",        "class_id": 4, "name": "Bebida Mango-Durazno Nebraska 460ml",     "slot_id": 5},
    {"sku_id": "sisi_cola",             "class_id": 5, "name": "Refresco Cola Sin Azucar Sisi 355ml",     "slot_id": 6},
    {"sku_id": "sun_paradise_naranja",  "class_id": 6, "name": "Bebida Naranja Sun Paradise 900ml",       "slot_id": 7},
]
```

---

### M4 — API Backend (FastAPI + WebSocket)
**Archivo:** `backend/main.py`

#### Endpoints REST
```
GET  /api/inventory              → InventoryState (JSON)
GET  /api/inventory/{sku_id}     → ProductStock (JSON)
GET  /api/events?limit=50        → list[InventoryEvent]
GET  /api/predictions            → list[StockPrediction]
GET  /api/heatmap                → HeatmapData
GET  /api/narratives?limit=10    → list[NarrativeMessage]
POST /api/inventory/reset        → Reset inventario
PUT  /api/config/threshold       → { "threshold": 0.20 }
```

#### WebSocket `/ws/live`
Mensajes push al frontend (JSON):
- `inventory_update` — Cambió el stock de un SKU
- `alert` — Un SKU cruzó el umbral
- `prediction_update` — Nueva predicción calculada
- `narrative` — Nueva narrativa generada
- `heatmap_update` — Datos de heatmap actualizados

#### WebSocket `/ws/video` o endpoint MJPEG
Frames con overlay a ≥5 FPS

#### Configuración
- CORS habilitado para `localhost:5173` y `localhost:3000`
- Broadcast a múltiples clientes WebSocket
- Host: `0.0.0.0`, Port: `8000`

### Mock para desarrollo sin M2
```python
# Generar eventos simulados cada 5 segundos
import random, uuid
from datetime import datetime

def mock_detection_event():
    skus = PRODUCTOS
    sku = random.choice(skus)
    return DetectionEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.RETIRO,
        sku_id=sku["sku_id"],
        sku_name=sku["name"],
        slot_id=sku["slot_id"],
        confidence=round(random.uniform(0.75, 0.99), 2),
        timestamp=datetime.now(),
        bbox=(100, 200, 300, 400),
        count_before=5,
        count_after=4
    )
```

### Prioridades
1. 🔴 InventoryEngine funcional (estado + decremento + alerta)
2. 🔴 GET /api/inventory + POST /api/inventory/reset
3. 🔴 WebSocket /ws/live con broadcast de inventory_update y alert
4. 🟡 GET /api/events + /api/predictions + /api/narratives
5. 🟡 WebSocket /ws/video (stream de frames)
6. 🟢 PUT /api/config/threshold

### Si terminas antes
Ayuda con: integración con M2, testing de WebSocket con frontend, edge cases (stock=0, doble retiro), estabilidad.
