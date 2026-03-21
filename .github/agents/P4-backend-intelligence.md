# Contexto para Copilot — P4: Backend Inteligencia (Módulos M6 + M7 + M8)

## Tu rol
Eres el responsable de los **módulos inteligentes** del sistema: la **predicción de desabasto**, el **heatmap de actividad** y la **narración automática**. Estos módulos son los **diferenciadores** que harán que nuestra solución destaque frente a los otros equipos (vale **30% de innovación** en la evaluación).

## Tus módulos

### M6 — Modelo Predictivo de Desabasto
**Archivo:** `backend/prediction_engine.py`

#### Input que recibes de M3 (Contrato C6)
```python
@dataclass
class SKUHistory:
    sku_id: str
    sku_name: str
    stock_current: int
    stock_initial: int        # 8
    events: list[datetime]    # Lista de timestamps de cada retiro
```

#### Output que produces
```python
@dataclass
class StockPrediction:
    sku_id: str
    sku_name: str
    stock_current: int
    rate_per_hour: float              # Tasa de retiro (unidades/hora)
    estimated_depletion: datetime | None  # Hora estimada de agotamiento
    minutes_remaining: float | None       # Minutos hasta agotamiento
    trend: str                        # "acelerando" | "estable" | "desacelerando"
    confidence: str                   # "alta" | "media" | "baja"
```

#### Algoritmo
```python
# Suavizado exponencial para la tasa de retiro
alpha = 0.3  # Configurable — más peso a eventos recientes

def calcular_prediccion(history: SKUHistory) -> StockPrediction:
    if len(history.events) < 2:
        return StockPrediction(..., minutes_remaining=None, confidence="baja")
    
    # Intervalos entre retiros en minutos
    intervalos = [(history.events[i+1] - history.events[i]).total_seconds() / 60
                  for i in range(len(history.events) - 1)]
    
    # Suavizado exponencial
    tasa = intervalos[0]
    for intervalo in intervalos[1:]:
        tasa = alpha * intervalo + (1 - alpha) * tasa
    
    minutos = tasa * history.stock_current
    rate_per_hour = 60 / tasa if tasa > 0 else 0
    
    # Tendencia: comparar primera mitad vs segunda mitad
    mid = len(intervalos) // 2
    if mid > 0:
        avg_old = sum(intervalos[:mid]) / mid
        avg_new = sum(intervalos[mid:]) / (len(intervalos) - mid)
        trend = "acelerando" if avg_new < avg_old * 0.8 else (
                "desacelerando" if avg_new > avg_old * 1.2 else "estable")
    
    # Confianza
    conf = "alta" if len(history.events) > 6 else ("media" if len(history.events) > 3 else "baja")
    
    return StockPrediction(...)
```

---

### M7 — Heatmap de Actividad
**Archivo:** `backend/heatmap_engine.py`

#### Input que recibes de M2 (Contrato C4)
```python
@dataclass
class InteractionEvent:
    slot_id: int
    sku_id: str
    region: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    timestamp: datetime
    interaction_type: str  # "hand_detected" | "product_moved"
```

#### Output que produces
```python
# Datos para el frontend
heatmap_data = {
    "slots": [
        {"slot_id": 1, "sku_id": "agua_burst", "activity_count": 2, "intensity": 0.25},
        {"slot_id": 3, "sku_id": "burst_energy", "activity_count": 8, "intensity": 1.00},
        ...
    ],
    "window_seconds": 300,
    "last_updated": "2026-03-21T14:32:01Z"
}
```

#### Lógica
- Acumular interacciones por slot
- Calcular intensidad relativa (slot más activo = 1.0, normalizado)
- Ventana temporal configurable (default 5 min, o "desde inicio")
- Actualizar cada 10 segundos (no saturar frontend)

---

### M8 — Narración Inteligente
**Archivo:** `backend/narrative_engine.py`

#### Input (Contrato C7)
```python
@dataclass
class NarrativeInput:
    inventory: InventoryState
    predictions: list[StockPrediction]
    recent_events: list[InventoryEvent]
```

#### Output
```python
@dataclass
class NarrativeMessage:
    message_id: str
    severity: str      # "info" | "warning" | "critical"
    text: str          # Texto en español, legible para humano
    sku_id: str | None
    timestamp: datetime
    icon: str          # Emoji
```

#### Templates de narrativa
```python
TEMPLATES = {
    "retiro": "📦 {sku_name} retirado del anaquel. Stock actual: {stock} unidades",
    "devolucion": "🔄 {sku_name} devuelto al anaquel. Stock ajustado: {before} → {after}",
    "alerta_umbral": "⚠️ ¡ALERTA! {sku_name} alcanzó el umbral crítico ({pct}%). Reponer urgente.",
    "prediccion": "🔮 {sku_name} se agotará en ~{minutes} min al ritmo actual ({trend})",
    "todo_ok": "✅ Todos los productos están por encima del umbral de seguridad",
    "resumen": "📊 Estado general: {n_alerta} producto(s) en alerta, {n_ok} OK. Último evento hace {ago}",
    "alta_demanda": "🔥 {sku_name} tiene alta demanda — {count} retiros en los últimos {window} min",
}
```

#### Reglas
- No repetir el mismo tipo de narrativa para el mismo SKU en < 30 segundos
- Generar automáticamente al detectar: retiro, devolución, alerta, predicción nueva
- Retener últimas 50 narrativas
- Asignar severidad: info (retiro normal), warning (umbral cercano), critical (umbral cruzado)

### Mock para desarrollo sin M3/M2
```python
# Historial fake para probar predicción
from datetime import datetime, timedelta
now = datetime.now()
fake_history = SKUHistory(
    sku_id="nachos_naturasol",
    sku_name="Nachos Con Sal Naturasol 200gr",
    stock_current=4,
    stock_initial=8,
    events=[now - timedelta(minutes=i*5) for i in range(4, 0, -1)]
)
```

### Prioridades
1. 🔴 PredictionEngine funcional (tasa + minutos restantes)
2. 🔴 NarrativeEngine con templates de retiro + alerta
3. 🟡 Tendencia (acelerando/estable/desacelerando)
4. 🟡 HeatmapEngine (acumulación + intensidad)
5. 🟡 Narrativa predictiva ("se agotará en...")
6. 🟢 Cooldown de narrativas repetidas

### Si terminas antes
Ayuda con: pulir narrativas, integración con M4 (API), agregar más templates, testing de predicción con datos reales, preparar pitch.
