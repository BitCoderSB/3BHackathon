"""
M3 — Motor de Inventario
Mantiene el estado de los 7 productos, aplica la lógica de negocio
y notifica a M4, M6, M8 vía callbacks (patrón observer).
"""

from collections import deque
from copy import copy
from datetime import datetime
from threading import Lock
from typing import Callable
import logging

from contracts import (
    EventType, DetectionEvent, ProductStock, InventoryState,
    InventoryEvent, SKUHistory,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
#  Catálogo de los 7 productos reales
# ─────────────────────────────────────────

PRODUCTOS = [
    {
        "sku_id": "agua_burst",            "class_id": 0, "slot_id": 1,
        "name": "Agua Natural Burst 1500ml",
        "src_product_id": 7746,   "barcode": 7502261250185,
        "presentation": "1500 ml", "product_type": "MP",
        "line_name": "Agua Natural", "group_name": "Water", "iventa": 6,
    },
    {
        "sku_id": "burst_energetica_roja", "class_id": 1, "slot_id": 2,
        "name": "Bebida Energetica Red Burst 473ml",
        "src_product_id": 11024,  "barcode": 7502261254411,
        "presentation": "473 ml",  "product_type": "MP",
        "line_name": "Energetica Isotonica", "group_name": "Beverages", "iventa": 1,
    },
    {
        "sku_id": "burst_energy",          "class_id": 2, "slot_id": 3,
        "name": "Bebida Energetica Original Burst Energy 600ml",
        "src_product_id": 22013,  "barcode": 7502261273047,
        "presentation": "600 ml",  "product_type": "MP",
        "line_name": "Energetica Isotonica", "group_name": "Beverages", "iventa": 12.5,
    },
    {
        "sku_id": "nachos_naturasol",      "class_id": 3, "slot_id": 4,
        "name": "Nachos Con Sal Naturasol 200gr",
        "src_product_id": 25996,  "barcode": 7503052023278,
        "presentation": "200 gr",  "product_type": "MC",
        "line_name": "Frituras", "group_name": "Snacks", "iventa": 22,
    },
    {
        "sku_id": "nebraska_mango",        "class_id": 4, "slot_id": 5,
        "name": "Bebida Mango-Durazno Nebraska 460ml",
        "src_product_id": 26449,  "barcode": 7502261273504,
        "presentation": "460 ml",  "product_type": "MP",
        "line_name": "Jugos y Bebidas", "group_name": "Beverages", "iventa": 14,
    },
    {
        "sku_id": "sisi_cola",             "class_id": 5, "slot_id": 6,
        "name": "Refresco Cola Sin Azucar Sisi 355ml",
        "src_product_id": 22287,  "barcode": 7502261272415,
        "presentation": "355 ml",  "product_type": "MP",
        "line_name": "Refrescos", "group_name": "Beverages", "iventa": 11,
    },
    {
        "sku_id": "sun_paradise_naranja",  "class_id": 6, "slot_id": 7,
        "name": "Bebida Naranja Sun Paradise 900ml",
        "src_product_id": 24338,  "barcode": 7502261269576,
        "presentation": "900 ml",  "product_type": "MP",
        "line_name": "Jugos y Bebidas", "group_name": "Beverages", "iventa": 18,
    },
]

STOCK_INITIAL       = 8
CONFIDENCE_THRESHOLD = 0.15     # umbral bajo: DetectionEngine ya valida consistencia (3 frames)
MIN_THRESHOLD        = 0.20     # alerta cuando stock <= 25% del inicial
MAX_EVENTS           = 1000    # máximo de eventos en memoria
MAX_TIMESTAMPS_PER_SKU = 500   # máximo de timestamps por SKU


# ─────────────────────────────────────────
#  Motor principal
# ─────────────────────────────────────────

class InventoryEngine:

    def __init__(
        self,
        stock_initial: int = STOCK_INITIAL,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        min_threshold: float = MIN_THRESHOLD,
    ):
        self.stock_initial        = stock_initial
        self.confidence_threshold = confidence_threshold
        self.min_threshold        = min_threshold

        self._lock = Lock()

        # Estado interno: { sku_id: ProductStock }
        self._stock: dict[str, ProductStock] = {}

        # Historial de eventos con tamaño limitado (para M4 y M6)
        self._events: deque[InventoryEvent] = deque(maxlen=MAX_EVENTS)

        # Historial de timestamps por SKU (para M6)
        self._event_timestamps: dict[str, deque[datetime]] = {}

        # Deduplicación de event_id
        self._processed_ids: set[str] = set()

        # Callbacks separados
        self._on_event_callbacks: list[Callable] = []
        self._on_alert_callbacks: list[Callable] = []

        self._init_stock()

    # ── Inicialización ───────────────────

    def _init_stock(self):
        for p in PRODUCTOS:
            self._stock[p["sku_id"]] = ProductStock(
                sku_id              = p["sku_id"],
                sku_name            = p["name"],
                slot_id             = p["slot_id"],
                stock_initial       = self.stock_initial,
                stock_current       = self.stock_initial,
                stock_min_threshold = self.min_threshold,
                is_alert            = False,
                last_event          = None,
            )
            self._event_timestamps[p["sku_id"]] = deque(maxlen=MAX_TIMESTAMPS_PER_SKU)

    # ── Observer pattern ─────────────────

    def on_event(self, callback: Callable):
        """Registra callback invocado tras cada evento. Firma: cb(event: InventoryEvent, stock: ProductStock)"""
        self._on_event_callbacks.append(callback)

    def on_alert(self, callback: Callable):
        """Registra callback invocado cuando se genera alerta. Firma: cb(event: InventoryEvent, stock: ProductStock)"""
        self._on_alert_callbacks.append(callback)

    def _notify_event(self, event: InventoryEvent, stock: ProductStock):
        for cb in self._on_event_callbacks:
            try:
                cb(event, stock)
            except Exception as e:
                logger.error(f"on_event callback error: {e}")

    def _notify_alert(self, event: InventoryEvent, stock: ProductStock):
        for cb in self._on_alert_callbacks:
            try:
                cb(event, stock)
            except Exception as e:
                logger.error(f"on_alert callback error: {e}")

    # ── Procesamiento de eventos ─────────

    def process_event(self, detection: DetectionEvent) -> InventoryEvent | None:
        """
        Punto de entrada principal. Recibe un DetectionEvent de M2.
        Retorna el InventoryEvent generado, o None si se ignoró/duplicó.
        """
        # Ignorar baja confianza
        if detection.confidence < self.confidence_threshold:
            logger.warning(
                f"Evento ignorado — confianza {detection.confidence:.2f} "
                f"< umbral {self.confidence_threshold:.2f} (sku={detection.sku_id})"
            )
            return None

        # Ignorar SKU desconocido
        if detection.sku_id not in self._stock:
            logger.error(f"SKU desconocido: {detection.sku_id}")
            return None

        with self._lock:
            # Deduplicar por event_id
            if detection.event_id in self._processed_ids:
                logger.warning(f"Evento duplicado ignorado: {detection.event_id}")
                return None
            self._processed_ids.add(detection.event_id)

            product = self._stock[detection.sku_id]
            stock_before = product.stock_current
            was_alert = product.is_alert

            # Aplicar lógica de negocio
            if detection.event_type == EventType.RETIRO:
                product.stock_current = max(0, product.stock_current - 1)

            elif detection.event_type == EventType.DEVOLUCION:
                product.stock_current = min(self.stock_initial, product.stock_current + 1)

            # Registrar timestamp (solo retiros — contrato C6)
            if detection.event_type == EventType.RETIRO:
                self._event_timestamps[detection.sku_id].append(detection.timestamp)

            # Recalcular alerta
            alert_level = self.stock_initial * self.min_threshold
            product.is_alert  = product.stock_current <= alert_level
            product.last_event = detection.timestamp

            # Registrar evento
            inv_event = InventoryEvent(
                event_id    = detection.event_id,
                event_type  = detection.event_type.value,
                sku_id      = detection.sku_id,
                sku_name    = detection.sku_name,
                slot_id     = detection.slot_id,
                stock_before = stock_before,
                stock_after  = product.stock_current,
                confidence  = detection.confidence,
                timestamp   = detection.timestamp,
            )
            self._events.append(inv_event)

            # Detectar transición a alerta
            alert_transition = product.is_alert and not was_alert

        logger.info(
            f"[{inv_event.event_type.upper()}] {detection.sku_name} "
            f"{stock_before} → {product.stock_current} "
            f"{'🚨 ALERTA' if alert_transition else ''}"
        )

        # Notificar observers (M4, M6, M8)
        self._notify_event(inv_event, product)
        if alert_transition:
            self._notify_alert(inv_event, product)

        return inv_event

    # ── Consultas ────────────────────────

    def get_state(self) -> InventoryState:
        with self._lock:
            return InventoryState(
                last_updated = datetime.now(),
                products     = [copy(p) for p in self._stock.values()],
            )

    def get_product(self, sku_id: str) -> ProductStock | None:
        with self._lock:
            p = self._stock.get(sku_id)
            return copy(p) if p else None

    def get_events(self, limit: int = 50) -> list[InventoryEvent]:
        with self._lock:
            return list(reversed(self._events))[:limit]

    def get_history(self, sku_id: str) -> SKUHistory | None:
        with self._lock:
            product = self._stock.get(sku_id)
            if not product:
                return None
            return SKUHistory(
                sku_id        = sku_id,
                sku_name      = product.sku_name,
                stock_current = product.stock_current,
                stock_initial = self.stock_initial,
                events        = list(self._event_timestamps[sku_id]),
            )

    def get_all_histories(self) -> list[SKUHistory]:
        return [self.get_history(sku_id) for sku_id in self._stock]

    # ── Analytics & Restock ──────────────

    def _get_producto_meta(self, sku_id: str) -> dict | None:
        for p in PRODUCTOS:
            if p["sku_id"] == sku_id:
                return p
        return None

    def get_analytics(self) -> dict:
        """KPIs en tiempo real del anaquel."""
        with self._lock:
            products = list(self._stock.values())
            total_capacity = self.stock_initial * len(products)
            total_current  = sum(p.stock_current for p in products)
            total_events   = len(self._events)

            # Conteo de retiros por SKU
            retiros_por_sku: dict[str, int] = {}
            for ev in self._events:
                if ev.event_type == "retiro":
                    retiros_por_sku[ev.sku_id] = retiros_por_sku.get(ev.sku_id, 0) + 1

            # Velocidad de rotación (eventos/minuto)
            if total_events >= 2:
                events_list = list(self._events)
                span = (events_list[-1].timestamp - events_list[0].timestamp).total_seconds()
                velocity = (total_events / span * 60) if span > 0 else 0.0
            else:
                velocity = 0.0

            # Producto más y menos vendido
            most_sold  = max(retiros_por_sku, key=retiros_por_sku.get) if retiros_por_sku else None
            least_sold = min(retiros_por_sku, key=retiros_por_sku.get) if retiros_por_sku else None

            # Fill rate por producto
            fill_rates = []
            for p in products:
                meta = self._get_producto_meta(p.sku_id)
                fill_rates.append({
                    "sku_id":       p.sku_id,
                    "sku_name":     p.sku_name,
                    "stock_current": p.stock_current,
                    "stock_initial": p.stock_initial,
                    "fill_rate":    round(p.stock_current / p.stock_initial, 2) if p.stock_initial else 0,
                    "retiros":      retiros_por_sku.get(p.sku_id, 0),
                    "iventa":       meta.get("iventa", 0) if meta else 0,
                })

            alerts_active = sum(1 for p in products if p.is_alert)

        return {
            "timestamp":         datetime.now().isoformat(),
            "total_capacity":    total_capacity,
            "total_current":     total_current,
            "fill_rate_global":  round(total_current / total_capacity, 2) if total_capacity else 0,
            "total_events":      total_events,
            "velocity_per_min":  round(velocity, 2),
            "alerts_active":     alerts_active,
            "most_sold_sku":     most_sold,
            "least_sold_sku":    least_sold,
            "products":          fill_rates,
        }

    def get_restock(self) -> list[dict]:
        """Prioriza qué productos reponer. Score más alto = más urgente."""
        with self._lock:
            recommendations = []
            for p in self._stock.values():
                meta = self._get_producto_meta(p.sku_id)
                iventa = meta.get("iventa", 1) if meta else 1

                units_missing = p.stock_initial - p.stock_current
                if units_missing == 0:
                    continue

                fill = p.stock_current / p.stock_initial if p.stock_initial else 1
                # Score: combina unidades faltantes, iventa y nivel de vaciado
                # Productos con alto iventa y bajo stock → score muy alto
                score = round(units_missing * iventa * (1 - fill), 1)

                recommendations.append({
                    "sku_id":        p.sku_id,
                    "sku_name":      p.sku_name,
                    "slot_id":       p.slot_id,
                    "stock_current": p.stock_current,
                    "stock_initial": p.stock_initial,
                    "units_missing": units_missing,
                    "fill_rate":     round(fill, 2),
                    "iventa":        iventa,
                    "priority_score": score,
                    "is_alert":      p.is_alert,
                    "urgency":       "CRITICA" if p.is_alert else ("MEDIA" if fill <= 0.5 else "BAJA"),
                })

            recommendations.sort(key=lambda r: r["priority_score"], reverse=True)
        return recommendations

    # ── Control ──────────────────────────

    def reset(self):
        """Vuelve todos los productos a stock_initial. Útil para demos."""
        with self._lock:
            for product in self._stock.values():
                product.stock_current = self.stock_initial
                product.is_alert      = False
                product.last_event    = None
            self._events.clear()
            self._processed_ids.clear()
            for sku_id in self._event_timestamps:
                self._event_timestamps[sku_id].clear()
        logger.info("Inventario reseteado a stock inicial.")

    def set_threshold(self, threshold: float):
        """Cambia el umbral de alerta en caliente (sin reiniciar)."""
        with self._lock:
            self.min_threshold = threshold
            for product in self._stock.values():
                product.stock_min_threshold = threshold
                alert_level   = self.stock_initial * threshold
                product.is_alert = product.stock_current <= alert_level
        logger.info(f"Umbral actualizado a {threshold:.0%}")


# ─────────────────────────────────────────
#  Demo / Smoke test
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uuid

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    engine = InventoryEngine()

    # ── Registrar callbacks on_event / on_alert ──
    alertas: list[InventoryEvent] = []

    def cb_event(event: InventoryEvent, stock: ProductStock):
        print(f"  [on_event] {event.sku_name}: {event.stock_before} → {event.stock_after}")

    def cb_alert(event: InventoryEvent, stock: ProductStock):
        alertas.append(event)
        print(f"  🚨 ALERTA: {event.sku_id} stock bajo (stock={event.stock_after})")

    engine.on_event(cb_event)
    engine.on_alert(cb_alert)

    sku      = "nachos_naturasol"
    sku_name = "Nachos Con Sal Naturasol 200gr"
    slot     = 4

    def _make_det(event_type: EventType) -> DetectionEvent:
        return DetectionEvent(
            event_id     = str(uuid.uuid4()),
            event_type   = event_type,
            sku_id       = sku,
            sku_name     = sku_name,
            slot_id      = slot,
            confidence   = 0.95,
            timestamp    = datetime.now(),
            bbox         = (100, 200, 300, 400),
            count_before = 0,
            count_after  = 0,
        )

    # ── 1) 5 retiros: stock 8→7→6→5→4→3 ──
    print("=" * 50)
    print("Simulando 5 retiros de nachos_naturasol")
    print("=" * 50)
    for i in range(1, 6):
        print(f"\n--- Retiro #{i} ---")
        engine.process_event(_make_det(EventType.RETIRO))
        prod = engine.get_product(sku)
        print(f"  stock_current={prod.stock_current}  is_alert={prod.is_alert}")

    # ── 2) Retiro extra: stock 3→2  ⇒  alerta (25% de 8 = 2) ──
    print(f"\n--- Retiro #6 (dispara alerta) ---")
    engine.process_event(_make_det(EventType.RETIRO))
    prod = engine.get_product(sku)
    print(f"  stock_current={prod.stock_current}  is_alert={prod.is_alert}")

    # ── 3) Devolución: stock 2→3 (restaurar para verificar get_state) ──
    print(f"\n--- Devolución (stock vuelve a 3) ---")
    engine.process_event(_make_det(EventType.DEVOLUCION))
    prod = engine.get_product(sku)
    print(f"  stock_current={prod.stock_current}  is_alert={prod.is_alert}")

    # ── 4) get_state(): 7 productos, 6 en stock=8, nachos en stock=3 ──
    print(f"\n{'=' * 50}")
    print("get_state() — Estado completo del inventario")
    print("=" * 50)
    state = engine.get_state()
    for p in state.products:
        flag = " ← ALERTA" if p.is_alert else ""
        print(f"  {p.sku_id:<28} slot={p.slot_id}  stock={p.stock_current}/{p.stock_initial}{flag}")

    # ── Verificaciones automáticas ──
    print(f"\n{'=' * 50}")
    print("Verificaciones")
    print("=" * 50)
    nachos = engine.get_product(sku)
    others = [p for p in state.products if p.sku_id != sku]

    assert nachos.stock_current == 3, f"Nachos debería estar en 3, está en {nachos.stock_current}"
    assert all(p.stock_current == 8 for p in others), "Los otros 6 productos deben estar en stock=8"
    assert len(alertas) > 0, "Debería haber al menos una alerta"
    assert any(a.stock_after == 2 for a in alertas), "Debería haber alerta cuando stock llega a 2"
    assert len(state.products) == 7, "Deben ser 7 productos"

    print(f"  ✔ Stock nachos = {nachos.stock_current}")
    print(f"  ✔ 6 productos en stock = 8")
    print(f"  ✔ Alertas generadas: {len(alertas)} (stock_after=2)")
    print(f"  ✔ Total productos: {len(state.products)}")
    print("\n✅ Todas las verificaciones pasaron.")