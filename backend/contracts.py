"""
Contratos compartidos — Tipos de datos del sistema de inventario.
Centraliza todas las dataclasses e enums usados entre módulos M2-M8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import numpy as np


# ─────────────────────────────────────────
#  C2 — Eventos de detección (M2 → M3)
# ─────────────────────────────────────────

class EventType(Enum):
    RETIRO = "retiro"
    DEVOLUCION = "devolucion"


@dataclass
class DetectionEvent:
    event_id: str
    event_type: EventType
    sku_id: str
    sku_name: str
    slot_id: int
    confidence: float
    timestamp: datetime
    bbox: tuple[int, int, int, int]
    count_before: int
    count_after: int


# ─────────────────────────────────────────
#  C3 — Resultado de detección (M2 interno)
# ─────────────────────────────────────────

@dataclass
class SlotDetection:
    sku_id: str
    sku_name: str
    slot_id: int
    bbox: tuple[int, int, int, int]
    confidence: float
    count: int
    stock_level: str  # "ok" | "warning" | "critical"


@dataclass
class DetectionResult:
    timestamp: float
    counts: dict[str, int]  # sku_id -> cantidad detectada
    detections: list[SlotDetection] = field(default_factory=list)


@dataclass
class AnnotatedFrame:
    frame: np.ndarray
    timestamp: float
    detections: list[SlotDetection]


# ─────────────────────────────────────────
#  C4 — Interacciones (M2 → M7)
# ─────────────────────────────────────────

@dataclass
class InteractionEvent:
    slot_id: int
    sku_id: str
    region: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    timestamp: datetime
    interaction_type: str  # "hand_detected" | "product_moved"


# ─────────────────────────────────────────
#  C5 — Estado de inventario (M3 → M4)
# ─────────────────────────────────────────

@dataclass
class ProductStock:
    sku_id: str
    sku_name: str
    slot_id: int
    stock_initial: int
    stock_current: int
    stock_min_threshold: float
    is_alert: bool
    last_event: datetime | None


@dataclass
class InventoryState:
    last_updated: datetime
    products: list[ProductStock]


@dataclass
class InventoryEvent:
    event_id: str
    event_type: str          # "retiro" | "devolucion"
    sku_id: str
    sku_name: str
    slot_id: int
    stock_before: int
    stock_after: int
    confidence: float
    timestamp: datetime


# ─────────────────────────────────────────
#  C6 — Historial para predicción (M3 → M6)
# ─────────────────────────────────────────

@dataclass
class SKUHistory:
    sku_id: str
    sku_name: str
    stock_current: int
    stock_initial: int  # 8
    events: list[datetime]  # Timestamps de cada retiro


@dataclass
class StockPrediction:
    sku_id: str
    sku_name: str
    stock_current: int
    rate_per_hour: float
    estimated_depletion: datetime | None
    minutes_remaining: float | None
    trend: str       # "acelerando" | "estable" | "desacelerando"
    confidence: str  # "alta" | "media" | "baja"


# ─────────────────────────────────────────
#  C7 — Mensajes narrativos (M8 → M4)
# ─────────────────────────────────────────

@dataclass
class NarrativeMessage:
    message_id: str
    severity: str       # "info" | "warning" | "critical"
    text: str           # Texto en español, legible para humano
    sku_id: str | None  # SKU relacionado (o None si es general)
    timestamp: datetime
    icon: str           # Emoji
