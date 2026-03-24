"""M6 — Motor Predictivo de Desabasto
Calcula cuándo se agotará cada producto usando suavizado exponencial.
"""

from datetime import datetime, timedelta

from contracts import SKUHistory, StockPrediction


class PredictionEngine:
    """Motor de predicción con suavizado exponencial."""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def predict(self, history: SKUHistory) -> StockPrediction:
        """Predice cuándo se agotará un SKU basándose en su historial de retiros."""
        # Caso: sin datos suficientes
        if len(history.events) < 2:
            return StockPrediction(
                sku_id=history.sku_id,
                sku_name=history.sku_name,
                stock_current=history.stock_current,
                rate_per_hour=0.0,
                estimated_depletion=None,
                minutes_remaining=None,
                trend="estable",
                confidence="baja",
            )

        # Caso: stock ya agotado
        if history.stock_current <= 0:
            return StockPrediction(
                sku_id=history.sku_id,
                sku_name=history.sku_name,
                stock_current=0,
                rate_per_hour=0.0,
                estimated_depletion=None,
                minutes_remaining=0.0,
                trend="estable",
                confidence="alta" if len(history.events) > 6 else "media",
            )

        # Ordenar eventos cronológicamente
        events_sorted = sorted(history.events)

        # Intervalos entre retiros consecutivos (en minutos)
        intervalos = [
            (events_sorted[i + 1] - events_sorted[i]).total_seconds() / 60
            for i in range(len(events_sorted) - 1)
        ]

        # Suavizado exponencial sobre los intervalos
        tasa = intervalos[0]
        for intervalo in intervalos[1:]:
            tasa = self.alpha * intervalo + (1 - self.alpha) * tasa

        # Calcular rate y minutos restantes
        rate_per_hour = 60 / tasa if tasa > 0 else 0.0
        minutes_remaining = tasa * history.stock_current if tasa > 0 else None

        # Hora estimada de agotamiento
        estimated_depletion = None
        if minutes_remaining is not None:
            estimated_depletion = datetime.now() + timedelta(minutes=minutes_remaining)

        # Tendencia: comparar primera mitad vs segunda mitad
        trend = self._calcular_tendencia(intervalos)

        # Confianza basada en cantidad de eventos
        confidence = self._calcular_confianza(len(history.events))

        return StockPrediction(
            sku_id=history.sku_id,
            sku_name=history.sku_name,
            stock_current=history.stock_current,
            rate_per_hour=round(rate_per_hour, 2),
            estimated_depletion=estimated_depletion,
            minutes_remaining=round(minutes_remaining, 1) if minutes_remaining else None,
            trend=trend,
            confidence=confidence,
        )

    def predict_all(self, histories: list[SKUHistory]) -> list[StockPrediction]:
        """Predice agotamiento para una lista de SKUs."""
        return [self.predict(h) for h in histories]

    def _calcular_tendencia(self, intervalos: list[float]) -> str:
        """Compara primera mitad vs segunda mitad de intervalos."""
        if len(intervalos) < 2:
            return "estable"

        mid = len(intervalos) // 2
        avg_old = sum(intervalos[:mid]) / mid
        avg_new = sum(intervalos[mid:]) / (len(intervalos) - mid)

        if avg_new < avg_old * 0.8:
            return "acelerando"
        elif avg_new > avg_old * 1.2:
            return "desacelerando"
        return "estable"

    def _calcular_confianza(self, n_eventos: int) -> str:
        """Determina confianza según cantidad de eventos (MVP M6-RF05)."""
        if n_eventos > 6:
            return "alta"
        elif n_eventos >= 3:
            return "media"
        return "baja"


if __name__ == "__main__":
    # Mock: 6 retiros de nachos con intervalos decrecientes (acelerando)
    # Intervalos: 5 min, 4 min, 3 min, 3 min, 2 min
    now = datetime.now()
    fake_history = SKUHistory(
        sku_id="nachos_naturasol",
        sku_name="Nachos Con Sal Naturasol 200gr",
        stock_current=2,
        stock_initial=8,
        events=[
            now - timedelta(minutes=17),  # retiro 1
            now - timedelta(minutes=12),  # retiro 2 (+5 min)
            now - timedelta(minutes=8),   # retiro 3 (+4 min)
            now - timedelta(minutes=5),   # retiro 4 (+3 min)
            now - timedelta(minutes=2),   # retiro 5 (+3 min)
            now,                          # retiro 6 (+2 min)
        ],
    )

    engine = PredictionEngine(alpha=0.3)
    pred = engine.predict(fake_history)

    print("=" * 50)
    print("  PREDICCIÓN DE DESABASTO — Fase 4.1")
    print("=" * 50)
    print(f"  SKU:                {pred.sku_id}")
    print(f"  Producto:           {pred.sku_name}")
    print(f"  Stock actual:       {pred.stock_current}/{fake_history.stock_initial}")
    print(f"  Tasa retiro:        {pred.rate_per_hour} unidades/hora")
    print(f"  Minutos restantes:  {pred.minutes_remaining}")
    print(f"  Agotamiento est.:   {pred.estimated_depletion.strftime('%H:%M:%S') if pred.estimated_depletion else 'N/A'}")
    print(f"  Tendencia:          {pred.trend}")
    print(f"  Confianza:          {pred.confidence}")
    print("=" * 50)

    # Verificaciones
    assert pred.rate_per_hour > 0, "FALLO: rate_per_hour debe ser > 0"
    assert pred.minutes_remaining is not None and pred.minutes_remaining > 0, "FALLO: minutes_remaining debe ser positivo"
    assert pred.trend == "acelerando", f"FALLO: trend debe ser 'acelerando', got '{pred.trend}'"
    assert pred.confidence == "alta", f"FALLO: confidence debe ser 'alta' (6 eventos), got '{pred.confidence}'"

    print("\n✅ Todas las verificaciones pasaron correctamente")
