"""
Fase 3.2 — API REST FastAPI
Expone el InventoryEngine vía endpoints HTTP.
"""

import time
import uuid
from dataclasses import asdict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from contracts import DetectionEvent, EventType
from inventory_engine import InventoryEngine

# ─────────────────────────────────────────
#  Instancia global
# ─────────────────────────────────────────

app = FastAPI(title="P3 BackendCore", version="0.1.0")
engine = InventoryEngine()
START_TIME = time.time()

# ─────────────────────────────────────────
#  CORS (desarrollo — allow all)
# ─────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
#  Endpoints
# ─────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "uptime": time.time() - START_TIME}


@app.get("/api/inventory")
def get_inventory():
    state = engine.get_state()
    return asdict(state)


@app.get("/api/inventory/{sku_id}")
def get_product(sku_id: str):
    product = engine.get_product(sku_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' no encontrado")
    return asdict(product)


@app.get("/api/events")
def get_events(limit: int = Query(default=50, ge=1, le=500)):
    events = engine.get_events(limit=limit)
    return [asdict(e) for e in events]


class SimulateEventBody(BaseModel):
    sku_id:     str
    event_type: str = Field(pattern="^(retiro|devolucion)$")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


@app.post("/api/events")
def simulate_event(body: SimulateEventBody):
    """Endpoint de simulación — inyecta un evento sin necesidad de M2 (cámara)."""
    product = engine.get_product(body.sku_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"SKU '{body.sku_id}' no encontrado")

    detection = DetectionEvent(
        event_id     = str(uuid.uuid4()),
        event_type   = EventType(body.event_type),
        sku_id       = body.sku_id,
        sku_name     = product.sku_name,
        slot_id      = product.slot_id,
        confidence   = body.confidence,
        timestamp    = datetime.now(),
        bbox         = (0, 0, 0, 0),
        count_before = 0,
        count_after  = 0,
    )
    inv_event = engine.process_event(detection)
    if inv_event is None:
        raise HTTPException(status_code=422, detail="Evento ignorado (confianza baja o duplicado)")
    return asdict(inv_event)


@app.get("/api/predictions")
def get_predictions():
    return []


@app.get("/api/heatmap")
def get_heatmap():
    return {}


@app.get("/api/narratives")
def get_narratives():
    return []


@app.post("/api/inventory/reset")
def reset_inventory():
    engine.reset()
    return {"status": "ok", "message": "Inventario reseteado a stock inicial"}


@app.get("/api/analytics")
def get_analytics():
    """KPIs en tiempo real: fill rate, velocidad, producto estrella, alertas."""
    return engine.get_analytics()


@app.get("/api/restock")
def get_restock():
    """Recomendación inteligente de reposición ordenada por prioridad."""
    return engine.get_restock()


# ─────────────────────────────────────────
#  Dashboard embebido
# ─────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>P3 BackendCore — Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
  h1 { text-align: center; margin-bottom: 8px; font-size: 1.6rem; color: #38bdf8; }
  .subtitle { text-align: center; color: #64748b; margin-bottom: 24px; font-size: 0.85rem; }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .kpi { background: #1e293b; border-radius: 12px; padding: 16px; text-align: center; border: 1px solid #334155; }
  .kpi .value { font-size: 2rem; font-weight: 700; color: #38bdf8; }
  .kpi .label { font-size: 0.75rem; color: #94a3b8; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
  .section-title { font-size: 1.1rem; color: #38bdf8; margin: 20px 0 12px; border-bottom: 1px solid #334155; padding-bottom: 6px; }
  .product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }
  .product-card { background: #1e293b; border-radius: 12px; padding: 16px; border: 1px solid #334155; }
  .product-card.alert { border-color: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.3); }
  .product-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .product-name { font-weight: 600; font-size: 0.9rem; }
  .product-slot { background: #334155; border-radius: 6px; padding: 2px 8px; font-size: 0.7rem; }
  .bar-bg { background: #334155; border-radius: 8px; height: 28px; position: relative; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 8px; transition: width 0.6s ease; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; }
  .bar-fill.green  { background: linear-gradient(90deg, #22c55e, #16a34a); }
  .bar-fill.yellow { background: linear-gradient(90deg, #eab308, #ca8a04); }
  .bar-fill.red    { background: linear-gradient(90deg, #ef4444, #dc2626); }
  .product-meta { display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.75rem; color: #94a3b8; }
  .restock-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  .restock-table th { text-align: left; padding: 8px 12px; background: #1e293b; color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; border-bottom: 1px solid #334155; }
  .restock-table td { padding: 8px 12px; border-bottom: 1px solid #1e293b; font-size: 0.85rem; }
  .badge { padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; }
  .badge.CRITICA { background: #dc2626; color: white; }
  .badge.MEDIA   { background: #ca8a04; color: white; }
  .badge.BAJA    { background: #334155; color: #94a3b8; }
  .refresh-note { text-align: center; color: #475569; font-size: 0.7rem; margin-top: 16px; }
</style>
</head>
<body>

<h1>&#x1F4E6; P3 BackendCore — Anaquel Inteligente</h1>
<p class="subtitle">Dashboard en tiempo real &bull; Auto-refresh cada 3s</p>

<div class="kpi-grid" id="kpis"></div>

<div class="section-title">&#x1F4CA; Estado del Inventario</div>
<div class="product-grid" id="products"></div>

<div class="section-title">&#x1F6D2; Recomendación de Reposición</div>
<table class="restock-table">
  <thead><tr><th>#</th><th>Producto</th><th>Stock</th><th>Faltan</th><th>iVenta</th><th>Score</th><th>Urgencia</th></tr></thead>
  <tbody id="restock"></tbody>
</table>

<p class="refresh-note" id="updated"></p>

<script>
async function fetchJSON(url) {
  const r = await fetch(url);
  return r.json();
}

function barColor(fill) {
  if (fill <= 0.25) return "red";
  if (fill <= 0.5) return "yellow";
  return "green";
}

async function refresh() {
  try {
    const [analytics, restock] = await Promise.all([
      fetchJSON("/api/analytics"),
      fetchJSON("/api/restock"),
    ]);

    // KPIs
    document.getElementById("kpis").innerHTML = `
      <div class="kpi"><div class="value">${analytics.total_current}/${analytics.total_capacity}</div><div class="label">Stock Total</div></div>
      <div class="kpi"><div class="value">${Math.round(analytics.fill_rate_global * 100)}%</div><div class="label">Fill Rate</div></div>
      <div class="kpi"><div class="value">${analytics.total_events}</div><div class="label">Eventos</div></div>
      <div class="kpi"><div class="value">${analytics.velocity_per_min}</div><div class="label">Eventos/min</div></div>
      <div class="kpi"><div class="value">${analytics.alerts_active}</div><div class="label">Alertas</div></div>
      <div class="kpi"><div class="value">${analytics.most_sold_sku || "—"}</div><div class="label">Más Vendido</div></div>
    `;

    // Products
    document.getElementById("products").innerHTML = analytics.products.map(p => {
      const fill = p.fill_rate;
      const pct = Math.round(fill * 100);
      const color = barColor(fill);
      const alertClass = fill <= 0.25 ? "alert" : "";
      return `
        <div class="product-card ${alertClass}">
          <div class="product-header">
            <span class="product-name">${p.sku_name}</span>
            <span class="product-slot">Slot ${p.sku_id.replace(/_/g, " ")}</span>
          </div>
          <div class="bar-bg">
            <div class="bar-fill ${color}" style="width:${Math.max(pct, 8)}%">${p.stock_current} / ${p.stock_initial}</div>
          </div>
          <div class="product-meta">
            <span>Fill: ${pct}%</span>
            <span>Retiros: ${p.retiros}</span>
            <span>iVenta: ${p.iventa}</span>
          </div>
        </div>`;
    }).join("");

    // Restock
    if (restock.length === 0) {
      document.getElementById("restock").innerHTML = '<tr><td colspan="7" style="text-align:center;color:#64748b;">Todo abastecido ✓</td></tr>';
    } else {
      document.getElementById("restock").innerHTML = restock.map((r, i) => `
        <tr>
          <td>${i + 1}</td>
          <td>${r.sku_name}</td>
          <td>${r.stock_current}/${r.stock_initial}</td>
          <td>${r.units_missing}</td>
          <td>${r.iventa}</td>
          <td><strong>${r.priority_score}</strong></td>
          <td><span class="badge ${r.urgency}">${r.urgency}</span></td>
        </tr>`).join("");
    }

    document.getElementById("updated").textContent = "Última actualización: " + new Date().toLocaleTimeString();
  } catch (e) {
    console.error("Refresh error:", e);
  }
}

refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>"""


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


# ─────────────────────────────────────────
#  Entrypoint
# ─────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
