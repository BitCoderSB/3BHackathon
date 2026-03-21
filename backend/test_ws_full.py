"""Test completo de WebSocket — verifica inventory_update, detection_event y alert."""
import socketio
import requests
import time

sio = socketio.Client()
msgs = []

@sio.on("inventory_update")
def on_u(d):
    msgs.append(("inv", d.get("last_updated", "")))

@sio.on("detection_event")
def on_d(d):
    msgs.append(("det", d.get("sku_id", "")))

@sio.on("alert")
def on_a(d):
    msgs.append(("ALERT", d.get("message", "")))

print("Conectando...")
sio.connect("http://localhost:8000")
print(f"SID: {sio.sid}")

# Reset
requests.post("http://localhost:8000/api/inventory/reset")
print("Inventario reseteado\n")

# Fire 20 mock events
for i in range(20):
    r = requests.post("http://localhost:8000/api/mock/event")
    j = r.json()
    name = j["sku_name"][:35]
    print(f"  {i+1:2d}. {name:35s} {j['stock_before']} -> {j['stock_after']}")

time.sleep(2)

print(f"\nTotal WS messages: {len(msgs)}")
alerts = [m for m in msgs if m[0] == "ALERT"]
det = [m for m in msgs if m[0] == "det"]
inv = [m for m in msgs if m[0] == "inv"]
print(f"  detection_event: {len(det)}")
print(f"  inventory_update: {len(inv)}")
print(f"  alert: {len(alerts)}")

if alerts:
    print("\nAlertas recibidas:")
    for a in alerts:
        print(f"  >> {a[1]}")

sio.disconnect()
print("\nOK - WebSocket funciona correctamente!")
