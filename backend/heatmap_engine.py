"""M7 — Heatmap de Actividad del Anaquel.

Registra interacciones por zona (slot) y genera un mapa de calor
normalizado con ventana temporal configurable.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


# --- Contrato de entrada (C4) ---

@dataclass
class InteractionEvent:
    slot_id: int
    sku_id: str
    region: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    timestamp: datetime
    interaction_type: str  # "hand_detected" | "product_moved"


class HeatmapEngine:
    """Acumula interacciones por slot y genera heatmap normalizado."""

    def __init__(self):
        self._interactions: list[InteractionEvent] = []

    def record(self, interaction: InteractionEvent):
        """Registra una interacción en el historial."""
        self._interactions.append(interaction)

    def get_heatmap(self, window_seconds: int = 300) -> dict:
        """Genera heatmap filtrado por ventana temporal.

        Retorna dict con slots ordenados por intensidad (mayor primero),
        donde el slot más activo tiene intensity=1.0.
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        # Filtrar interacciones dentro de la ventana
        recent = [i for i in self._interactions if i.timestamp >= cutoff]

        # Contar por slot_id
        counts: dict[int, dict] = {}
        for interaction in recent:
            sid = interaction.slot_id
            if sid not in counts:
                counts[sid] = {"slot_id": sid, "sku_id": interaction.sku_id, "activity_count": 0}
            counts[sid]["activity_count"] += 1

        # Normalizar intensidad
        max_count = max((s["activity_count"] for s in counts.values()), default=0)

        slots = []
        for slot_data in counts.values():
            intensity = slot_data["activity_count"] / max_count if max_count > 0 else 0.0
            slots.append({
                "slot_id": slot_data["slot_id"],
                "sku_id": slot_data["sku_id"],
                "activity_count": slot_data["activity_count"],
                "intensity": round(intensity, 2),
            })

        # Ordenar por intensidad descendente
        slots.sort(key=lambda s: s["intensity"], reverse=True)

        return {
            "slots": slots,
            "window_seconds": window_seconds,
            "last_updated": now.isoformat(),
        }

    def reset(self):
        """Limpia todas las interacciones."""
        self._interactions.clear()


# --- Test manual ---

if __name__ == "__main__":
    engine = HeatmapEngine()
    now = datetime.now()

    print("=" * 60)
    print("  FASE 4.3 — Test HeatmapEngine")
    print("=" * 60)

    # Registrar 10 interacciones: 5 en slot 3, 3 en slot 1, 2 en slot 5
    for i in range(5):
        engine.record(InteractionEvent(
            slot_id=3, sku_id="burst_energy",
            region=(300, 0, 400, 200), timestamp=now - timedelta(seconds=i * 10),
            interaction_type="product_moved",
        ))
    for i in range(3):
        engine.record(InteractionEvent(
            slot_id=1, sku_id="agua_burst",
            region=(0, 0, 100, 200), timestamp=now - timedelta(seconds=i * 10),
            interaction_type="hand_detected",
        ))
    for i in range(2):
        engine.record(InteractionEvent(
            slot_id=5, sku_id="sisi_cola",
            region=(500, 0, 600, 200), timestamp=now - timedelta(seconds=i * 10),
            interaction_type="product_moved",
        ))

    heatmap = engine.get_heatmap(window_seconds=300)

    print(f"\n  Ventana: {heatmap['window_seconds']}s")
    print(f"  last_updated: {heatmap['last_updated']}")
    print(f"  Slots ({len(heatmap['slots'])}):")
    for s in heatmap["slots"]:
        print(f"    slot {s['slot_id']} ({s['sku_id']:20s}): "
              f"count={s['activity_count']}, intensity={s['intensity']}")

    # Verificaciones
    slot_map = {s["slot_id"]: s for s in heatmap["slots"]}
    assert slot_map[3]["intensity"] == 1.0, f"slot 3 debe ser 1.0, got {slot_map[3]['intensity']}"
    assert slot_map[1]["intensity"] == 0.6, f"slot 1 debe ser 0.6, got {slot_map[1]['intensity']}"
    assert slot_map[5]["intensity"] == 0.4, f"slot 5 debe ser 0.4, got {slot_map[5]['intensity']}"

    # Verificar ISO timestamp
    datetime.fromisoformat(heatmap["last_updated"])
    print("\n  Verificaciones OK: intensidades y timestamp ISO válidos")

    print()
    print("*" * 60)
    print("  TODOS LOS TESTS PASARON ✓")
    print("*" * 60)
