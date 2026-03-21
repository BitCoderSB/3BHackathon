"""M8 — Motor de Narración Inteligente.

Genera mensajes narrativos en español a partir de eventos de inventario,
predicciones y alertas. Incluye cooldown para evitar spam.
"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid


# --- Contrato de salida (C7) ---

@dataclass
class NarrativeMessage:
    message_id: str
    severity: str       # "info" | "warning" | "critical"
    text: str           # Texto en español, legible para humano
    sku_id: str | None  # SKU relacionado (o None si es general)
    timestamp: datetime
    icon: str           # Emoji


# --- Templates ---

TEMPLATES = {
    "retiro": "📦 {sku_name} retirado del anaquel. Stock actual: {stock} unidades",
    "devolucion": "🔄 {sku_name} devuelto al anaquel. Stock ajustado: {before} → {after}",
    "alerta_umbral": "⚠️ ¡ALERTA! {sku_name} alcanzó el umbral crítico ({pct}%). Reponer urgente.",
    "prediccion": "🔮 {sku_name} se agotará en ~{minutes} min al ritmo actual",
    "todo_ok": "✅ Todos los productos están por encima del umbral de seguridad",
    "resumen": "📊 Estado general: {n_alerta} producto(s) en alerta, {n_ok} OK. Último evento hace {ago}",
    "alta_demanda": "🔥 {sku_name} tiene alta demanda — {count} retiros en los últimos {window} min",
}

# Mapeo tipo → severity
SEVERITY_MAP = {
    "retiro": "info",
    "devolucion": "info",
    "alerta_umbral": "critical",
    "prediccion": "warning",
    "todo_ok": "info",
    "resumen": "info",
    "alta_demanda": "warning",
}

# Mapeo tipo → icono
ICON_MAP = {
    "retiro": "📦",
    "devolucion": "🔄",
    "alerta_umbral": "⚠️",
    "prediccion": "🔮",
    "todo_ok": "✅",
    "resumen": "📊",
    "alta_demanda": "🔥",
}


class NarrativeEngine:
    """Genera narrativas en español para el dashboard."""

    def __init__(self, cooldown_seconds: float = 30.0):
        self._history: list[NarrativeMessage] = []
        self._cooldown: dict[str, datetime] = {}  # "tipo:sku_id" → last timestamp
        self._cooldown_seconds = cooldown_seconds

    # --- Método principal ---

    def generate(self, event_type: str, **kwargs) -> NarrativeMessage | None:
        """Genera una narrativa. Retorna None si está en cooldown."""
        if event_type not in TEMPLATES:
            raise ValueError(f"Tipo de evento desconocido: {event_type}")

        # Cooldown: clave = tipo:sku_id
        sku_id = kwargs.get("sku_id", kwargs.get("sku_name", ""))
        cooldown_key = f"{event_type}:{sku_id}"
        now = datetime.now()

        if cooldown_key in self._cooldown:
            elapsed = (now - self._cooldown[cooldown_key]).total_seconds()
            if elapsed < self._cooldown_seconds:
                return None  # Bloqueada por cooldown

        # Generar texto
        text = TEMPLATES[event_type].format(**kwargs)
        severity = SEVERITY_MAP[event_type]
        icon = ICON_MAP[event_type]

        msg = NarrativeMessage(
            message_id=uuid.uuid4().hex[:12],
            severity=severity,
            text=text,
            sku_id=sku_id if sku_id else None,
            timestamp=now,
            icon=icon,
        )

        # Registrar cooldown y guardar en historial
        self._cooldown[cooldown_key] = now
        self._history.append(msg)

        return msg

    # --- Consultas ---

    def get_recent(self, limit: int = 50) -> list[NarrativeMessage]:
        """Retorna las últimas N narrativas (más reciente primero)."""
        return list(reversed(self._history[-limit:]))

    def clear(self):
        """Limpia historial y cooldowns."""
        self._history.clear()
        self._cooldown.clear()


# --- Test manual ---

if __name__ == "__main__":
    engine = NarrativeEngine(cooldown_seconds=30.0)

    print("=" * 60)
    print("  FASE 4.2 — Test NarrativeEngine")
    print("=" * 60)

    # 1. Retiro
    print("\n1) Narrativa de RETIRO:")
    msg1 = engine.generate("retiro", sku_name="nachos_naturasol", stock=4)
    assert msg1 is not None
    print(f"   {msg1.icon} [{msg1.severity}] {msg1.text}")
    assert msg1.severity == "info"

    # 2. Alerta umbral
    print("\n2) Narrativa de ALERTA:")
    msg2 = engine.generate("alerta_umbral", sku_name="nachos_naturasol", pct=25)
    assert msg2 is not None
    print(f"   {msg2.icon} [{msg2.severity}] {msg2.text}")
    assert msg2.severity == "critical"

    # 3. Predicción
    print("\n3) Narrativa de PREDICCIÓN:")
    msg3 = engine.generate("prediccion", sku_name="nachos_naturasol", minutes=15)
    assert msg3 is not None
    print(f"   {msg3.icon} [{msg3.severity}] {msg3.text}")
    assert msg3.severity == "warning"

    # 4. Intento de alerta repetida (cooldown)
    print("\n4) Intento de ALERTA repetida (< 30s):")
    msg4 = engine.generate("alerta_umbral", sku_name="nachos_naturasol", pct=25)
    if msg4 is None:
        print("   ⏳ Bloqueada por cooldown — OK")
    else:
        raise AssertionError("Debería haber sido bloqueada por cooldown")

    # 5. Verificar historial
    print("\n5) Narrativas recientes:")
    recientes = engine.get_recent()
    print(f"   Total: {len(recientes)}")
    for m in recientes:
        print(f"   • {m.icon} [{m.severity:8s}] {m.text}")

    assert len(recientes) == 3, f"Esperaba 3, got {len(recientes)}"

    print()
    print("*" * 60)
    print("  TODOS LOS TESTS PASARON ✓")
    print("*" * 60)
