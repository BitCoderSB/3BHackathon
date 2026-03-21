"""Test INT-3 — Inventario → Inteligencia vía WebSocket"""
import time
import requests
import socketio

sio = socketio.Client()
results = {"updates": [], "predictions": [], "narratives": [], "alerts": [], "heatmaps": []}

@sio.on("inventory_update")
def on_update(data):
    results["updates"].append(data)

@sio.on("prediction_update")
def on_prediction(data):
    results["predictions"].append(data)

@sio.on("narrative")
def on_narrative(data):
    results["narratives"].append(data)

@sio.on("alert")
def on_alert(data):
    results["alerts"].append(data)

@sio.on("heatmap_update")
def on_heatmap(data):
    results["heatmaps"].append(data)

BASE = "http://localhost:8000"
print("Conectando...")
sio.connect(BASE)
print("Conectado!")

# Reset inventario
requests.post(f"{BASE}/api/inventory/reset")
print("Inventario reseteado\n")

# Disparar 4 retiros del mismo producto (para generar predicción útil)
for i in range(4):
    r = requests.post(f"{BASE}/api/events", json={
        "sku_id": "nachos_naturasol", "event_type": "retiro", "confidence": 0.95
    })
    print(f"Retiro {i+1}: {r.json()['stock_before']} -> {r.json()['stock_after']}")
    time.sleep(0.5)

time.sleep(1.5)

print(f"\n{'='*50}")
print(f"  RESULTADOS WebSocket")
print(f"{'='*50}")
print(f"  inventory_update:  {len(results['updates'])}")
print(f"  prediction_update: {len(results['predictions'])}")
print(f"  narrative:         {len(results['narratives'])}")
print(f"  heatmap_update:    {len(results['heatmaps'])}")
print(f"  alert:             {len(results['alerts'])}")

# Verificar predicciones
if results["predictions"]:
    last_preds = results["predictions"][-1]
    nachos_pred = next((p for p in last_preds if p["sku_id"] == "nachos_naturasol"), None)
    if nachos_pred:
        print(f"\n  Predicción nachos_naturasol:")
        print(f"    rate_per_hour:      {nachos_pred['rate_per_hour']}")
        print(f"    minutes_remaining:  {nachos_pred['minutes_remaining']}")
        print(f"    trend:              {nachos_pred['trend']}")
        print(f"    confidence:         {nachos_pred['confidence']}")

# Verificar narrativas
if results["narratives"]:
    print(f"\n  Narrativas recibidas:")
    for n in results["narratives"]:
        print(f"    {n.get('icon','')} [{n['severity']}] {n['text']}")

# Verificar REST endpoints
print(f"\n{'='*50}")
print(f"  VERIFICACIÓN REST")
print(f"{'='*50}")

preds_rest = requests.get(f"{BASE}/api/predictions").json()
print(f"  GET /api/predictions: {len(preds_rest)} predicciones")
nachos_rest = next((p for p in preds_rest if p["sku_id"] == "nachos_naturasol"), None)
if nachos_rest:
    print(f"    nachos rate: {nachos_rest['rate_per_hour']} u/h, mins: {nachos_rest['minutes_remaining']}")

narrs_rest = requests.get(f"{BASE}/api/narratives").json()
print(f"  GET /api/narratives: {len(narrs_rest)} mensajes")

heatmap_rest = requests.get(f"{BASE}/api/heatmap").json()
print(f"  GET /api/heatmap: {len(heatmap_rest.get('slots', []))} slots activos")

sio.disconnect()

# Validaciones finales
ok = True
if len(results["predictions"]) < 1:
    print("\nFALLO: No se recibieron prediction_update")
    ok = False
if len(results["narratives"]) < 1:
    print("\nFALLO: No se recibieron narratives")
    ok = False
if nachos_pred and nachos_pred.get("minutes_remaining") is None:
    print("\nFALLO: minutes_remaining es None (debería tener valor con 4 retiros)")
    ok = False

print(f"\n{'*'*50}")
print(f"  {'TEST INT-3 PASÓ ✓' if ok else 'TEST INT-3 FALLÓ ✗'}")
print(f"{'*'*50}")
