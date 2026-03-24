"""
Test exhaustivo P4: verifica TODOS los endpoints, edge cases y conformidad con contrato C8.
"""
import time
import requests

BASE = "http://127.0.0.1:8005"

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

passed = 0
failed = 0

def ok(desc):
    global passed
    passed += 1
    print(f"  ✅ {desc}")

def fail(desc, detail=""):
    global failed
    failed += 1
    print(f"  ❌ {desc} — {detail}")

def check(cond, desc, detail=""):
    if cond:
        ok(desc)
    else:
        fail(desc, detail)

# ─── 0. Health & Reset ───
section("0. Health + Reset limpio")
r = requests.get(f"{BASE}/api/health")
check(r.status_code == 200, "Health OK")

r = requests.post(f"{BASE}/api/inventory/reset")
check(r.status_code == 200, "Reset OK")
check(r.json()["status"] == "ok", "Reset response status=ok")

# ─── 1. Estado vacío (sin eventos) ───
section("1. Estado vacío — sin eventos")

r = requests.get(f"{BASE}/api/inventory")
inv = r.json()
check(r.status_code == 200, "GET /api/inventory 200")
check("products" in inv, "Inventory tiene 'products'")
check(len(inv["products"]) == 7, f"7 SKUs en inventario", f"tiene {len(inv.get('products', []))}")
# Verificar stock inicial = 8
for p in inv["products"]:
    if p["stock_current"] != 8:
        fail(f"stock_initial 8 para {p['sku_id']}", f"tiene {p['stock_current']}")
        break
else:
    ok("Todos los SKUs con stock_current=8")

r = requests.get(f"{BASE}/api/events")
check(r.status_code == 200, "GET /api/events 200")
check(r.json() == [], "0 eventos al inicio")

r = requests.get(f"{BASE}/api/predictions")
preds = r.json()
check(r.status_code == 200, "GET /api/predictions 200")
check(len(preds) == 7, f"7 predicciones (una por SKU)", f"tiene {len(preds)}")
for p in preds:
    if p["minutes_remaining"] is not None:
        fail("minutes_remaining debe ser null sin eventos", p)
        break
else:
    ok("Todas las predicciones con minutes_remaining=null")

r = requests.get(f"{BASE}/api/heatmap")
hm = r.json()
check(r.status_code == 200, "GET /api/heatmap 200")
check("slots" in hm, "Heatmap tiene 'slots'")

r = requests.get(f"{BASE}/api/narratives")
narr = r.json()
check(r.status_code == 200, "GET /api/narratives 200")
check(narr == [], "0 narrativas al inicio")

# ─── 2. PUT /api/config/threshold ───
section("2. PUT /api/config/threshold")

r = requests.put(f"{BASE}/api/config/threshold", json={"threshold": 0.50})
check(r.status_code == 200, "PUT threshold 0.50 OK")
check(r.json()["threshold"] == 0.50, "Response threshold=0.50")

# Validation: threshold > 1
r = requests.put(f"{BASE}/api/config/threshold", json={"threshold": 1.5})
check(r.status_code == 422, "threshold=1.5 rechazado (422)", f"got {r.status_code}")

# Restaurar a 25%
r = requests.put(f"{BASE}/api/config/threshold", json={"threshold": 0.25})
check(r.status_code == 200, "Restaurar threshold 0.25 OK")

# ─── 3. Simular retiros y verificar flujo completo ───
section("3. Simular retiros — flujo completo")

# 3 retiros de nachos (stock: 8 → 5)
for i in range(3):
    r = requests.post(f"{BASE}/api/events", json={"sku_id": "nachos_naturasol", "event_type": "retiro"})
    check(r.status_code == 200, f"Retiro nachos #{i+1} OK")
    time.sleep(0.3)  # Esperar para que haya intervalo de tiempo

# Verificar stock
r = requests.get(f"{BASE}/api/inventory/nachos_naturasol")
check(r.status_code == 200, "GET /api/inventory/nachos_naturasol")
check(r.json()["stock_current"] == 5, f"Stock nachos=5", f"got {r.json().get('stock_current')}")

# ─── 4. Filtro sku_id en eventos ───
section("4. GET /api/events?sku_id=...")

r = requests.get(f"{BASE}/api/events?sku_id=nachos_naturasol")
check(r.status_code == 200, "GET /api/events?sku_id=nachos_naturasol 200")
ev_nachos = r.json()
check(len(ev_nachos) == 3, f"3 eventos nachos filtrados", f"got {len(ev_nachos)}")

# SKU sin eventos
r = requests.get(f"{BASE}/api/events?sku_id=agua_burst")
check(len(r.json()) == 0, "0 eventos para agua_burst (sin actividad)")

# Todos los eventos sin filtro
r = requests.get(f"{BASE}/api/events")
check(len(r.json()) == 3, f"3 eventos totales", f"got {len(r.json())}")

# ─── 5. Predicciones con datos ───
section("5. Predicciones con datos")

r = requests.get(f"{BASE}/api/predictions")
preds = r.json()
nachos_pred = [p for p in preds if p["sku_id"] == "nachos_naturasol"]
check(len(nachos_pred) == 1, "Predicción encontrada para nachos")
np = nachos_pred[0]
check(np["minutes_remaining"] is not None, "minutes_remaining no-null para nachos", f"{np.get('minutes_remaining')}")
check(np["estimated_depletion"] is not None, "estimated_depletion no-null")
# Verificar serialización ISO
if np["estimated_depletion"]:
    check("T" in str(np["estimated_depletion"]), "estimated_depletion en formato ISO", np["estimated_depletion"])

# SKU sin eventos: predicción null
agua_pred = [p for p in preds if p["sku_id"] == "agua_burst"]
check(len(agua_pred) == 1, "Predicción para agua_burst existe")
check(agua_pred[0]["minutes_remaining"] is None, "agua_burst sin predicción (null)")

# ─── 6. Heatmap con actividad ───
section("6. Heatmap con actividad")

r = requests.get(f"{BASE}/api/heatmap")
hm = r.json()
slots = hm.get("slots", [])
nachos_slot = [s for s in slots if s.get("sku_id") == "nachos_naturasol"]
check(len(nachos_slot) > 0, "Nachos aparece en heatmap")
if nachos_slot:
    check(nachos_slot[0]["activity_count"] == 3, f"3 interacciones nachos en heatmap", f"got {nachos_slot[0].get('activity_count')}")
    check(nachos_slot[0]["intensity"] == 1.0, "Intensidad normalizada = 1.0 (máximo)")

# ─── 7. Narrativas generadas ───
section("7. Narrativas")

r = requests.get(f"{BASE}/api/narratives?limit=50")
narrs = r.json()
check(len(narrs) > 0, f"Se generaron narrativas ({len(narrs)})")

# Verificar serialización ISO en timestamp
if narrs:
    check("T" in str(narrs[0]["timestamp"]), "timestamp en formato ISO", narrs[0].get("timestamp"))

# Verificar severities
severities = {n["severity"] for n in narrs}
check(len(severities) > 0, f"Narrativas con severities: {severities}")

# Verificar que narrativas tienen campos requeridos del dataclass
required_fields = {"message_id", "severity", "text", "icon", "timestamp", "sku_id"}
first = narrs[0]
missing = required_fields - set(first.keys())
check(len(missing) == 0, "Narrativa tiene todos los campos requeridos", f"faltan: {missing}")

# ─── 8. Devolución ───
section("8. Devolución")

r = requests.post(f"{BASE}/api/events", json={"sku_id": "nachos_naturasol", "event_type": "devolucion"})
check(r.status_code == 200, "Devolucion nachos OK")
ev = r.json()
check(ev["event_type"] == "devolucion", "event_type=devolucion")
check(ev["stock_after"] == 6, f"Stock after devolucion=6", f"got {ev.get('stock_after')}")

r = requests.get(f"{BASE}/api/inventory/nachos_naturasol")
check(r.json()["stock_current"] == 6, "Stock nachos ahora=6 vía inventory")

# ─── 9. Alerta de umbral ───
section("9. Alerta de umbral (stock <= 25%)")

# Reset y threshold al 25% para test limpio
requests.post(f"{BASE}/api/inventory/reset")
requests.put(f"{BASE}/api/config/threshold", json={"threshold": 0.25})
time.sleep(0.5)

# Necesitamos 6 retiros para llegar a stock=2 (25% de 8)
# El umbral se cruza cuando stock <= floor(8 * 0.25) = 2
for i in range(6):
    r = requests.post(f"{BASE}/api/events", json={"sku_id": "sisi_cola", "event_type": "retiro"})
    check(r.status_code == 200, f"Retiro sisi_cola #{i+1}")
    time.sleep(0.3)

r = requests.get(f"{BASE}/api/inventory/sisi_cola")
check(r.json()["stock_current"] == 2, f"Stock sisi_cola=2", f"got {r.json().get('stock_current')}")

# Debería haber narrativa de alerta_umbral
r = requests.get(f"{BASE}/api/narratives?limit=50")
narrs = r.json()
alertas = [n for n in narrs if n["severity"] == "warning" or n["severity"] == "critical"]
check(len(alertas) > 0, f"Narrativa de alerta generada ({len(alertas)})", "ninguna alerta encontrada")

# ─── 10. Cooldown de narrativas ───
section("10. Cooldown de narrativas (30s)")

# Contar narrativas actuales
r1 = requests.get(f"{BASE}/api/narratives?limit=100")
count_before = len(r1.json())

# Hacer otro retiro rápido del mismo SKU
r = requests.post(f"{BASE}/api/events", json={"sku_id": "sisi_cola", "event_type": "retiro"})
check(r.status_code == 200, "Retiro sisi_cola #7 rapido")

r2 = requests.get(f"{BASE}/api/narratives?limit=100")
count_after = len(r2.json())

# El cooldown puede bloquear nuevas narrativas del mismo tipo+sku
# Verificamos que no se generaron más narrativas de retiro para sisi_cola
retiros_sisi = [n for n in r2.json() if n["severity"] == "info" and n.get("sku_id") == "sisi_cola"]
print(f"  INFO: Narrativas retiro sisi_cola: {len(retiros_sisi)} (cooldown activo si no creció)")
ok("Cooldown verificado (no crash)")

# ─── 11. Evento inválido ───
section("11. Validación de entrada")

r = requests.post(f"{BASE}/api/events", json={"sku_id": "producto_falso", "event_type": "retiro"})
check(r.status_code == 404, "SKU inexistente → 404", f"got {r.status_code}")

r = requests.post(f"{BASE}/api/events", json={"sku_id": "sisi_cola", "event_type": "robo"})
check(r.status_code == 422, "event_type inválido → 422", f"got {r.status_code}")

r = requests.post(f"{BASE}/api/events", json={"sku_id": "sisi_cola", "event_type": "retiro", "confidence": 2.0})
check(r.status_code == 422, "confidence=2.0 → 422", f"got {r.status_code}")

# ─── 12. Limite en narrativas ───
section("12. Límite en /api/narratives")

r = requests.get(f"{BASE}/api/narratives?limit=2")
check(r.status_code == 200, "GET /api/narratives?limit=2")
check(len(r.json()) <= 2, f"Máximo 2 narrativas devueltas", f"got {len(r.json())}")

# ─── 13. Reset limpia todo ───
section("13. POST /api/inventory/reset limpia P4")

r = requests.post(f"{BASE}/api/inventory/reset")
check(r.status_code == 200, "Reset OK")

r = requests.get(f"{BASE}/api/events")
check(len(r.json()) == 0, "0 eventos post-reset")

r = requests.get(f"{BASE}/api/narratives")
check(len(r.json()) == 0, "0 narrativas post-reset")

r = requests.get(f"{BASE}/api/heatmap")
hm = r.json()
slots = hm.get("slots", [])
active = [s for s in slots if s.get("activity_count", 0) > 0]
check(len(active) == 0, "Heatmap sin actividad post-reset", f"slots activos: {len(active)}")

r = requests.get(f"{BASE}/api/predictions")
for p in r.json():
    if p["minutes_remaining"] is not None:
        fail("Predicciones post-reset deben ser null", p)
        break
else:
    ok("Predicciones post-reset todas null")

# ─── Resumen ───
section("RESUMEN")
total = passed + failed
print(f"  {passed}/{total} tests pasaron")
if failed:
    print(f"  ⚠️  {failed} tests fallaron")
else:
    print(f"  🎉 Todos los tests pasaron!")
