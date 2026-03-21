"""Test rápido de WebSocket — Fase 3.3"""
import time
import requests
import socketio

sio = socketio.Client()
results = []

@sio.on("inventory_update")
def on_update(data):
    results.append(("UPDATE", data))

@sio.on("alert")
def on_alert(data):
    results.append(("ALERT", data))

@sio.on("detection_event")
def on_detection(data):
    results.append(("DETECTION", data))

print("Conectando a http://localhost:8000 ...")
sio.connect("http://localhost:8000")
print("Conectado!")

# Reset inventario primero
requests.post("http://localhost:8000/api/inventory/reset")
print("Inventario reseteado")

# Disparar suficientes eventos mock para generar alertas
for i in range(20):
    r = requests.post("http://localhost:8000/api/mock/event")
    print(f"Mock {i+1}: {r.json()['status']}")
    time.sleep(0.2)

time.sleep(1)

print(f"\nEventos WebSocket recibidos: {len(results)}")
for kind, data in results:
    evt = data.get("event", data)
    sku = evt.get("sku_id", "?")
    before = evt.get("stock_before", "?")
    after = evt.get("stock_after", "?")
    print(f"  [{kind}] {sku}: {before} -> {after}")

alerts = [r for r in results if r[0] == "ALERT"]
updates = [r for r in results if r[0] == "UPDATE"]
print(f"\n  - inventory_update: {len(updates)}")
print(f"  - alert: {len(alerts)}")
if alerts:
    for a in alerts:
        evt = a[1]["event"]
        stk = a[1]["stock"]
        print(f"  ALERTA: {evt['sku_id']} stock={stk['stock_current']}/{stk['stock_initial']}")

sio.disconnect()
print("\nTest completado OK!" if len(alerts) > 0 else "\nFALLO: no se recibieron alertas")
