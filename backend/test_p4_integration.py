"""Test de integración P4 — verifica que predictions, heatmap y narratives
funcionan a través de la API tras simular eventos."""

import requests
import time

BASE = "http://localhost:8000"


def main():
    # 0. Reset
    requests.post(f"{BASE}/api/inventory/reset")
    print("Inventario reseteado\n")

    # 1. Simular 3 retiros de nachos_naturasol
    print("=== Simulando 3 retiros de nachos_naturasol ===")
    for i in range(3):
        r = requests.post(f"{BASE}/api/events", json={"sku_id": "nachos_naturasol", "event_type": "retiro"})
        d = r.json()
        print(f"  Retiro {i+1}: {d['stock_before']} -> {d['stock_after']}")
        time.sleep(0.5)

    # 2. Simular 2 retiros de agua_burst
    print("\n=== Simulando 2 retiros de agua_burst ===")
    for i in range(2):
        r = requests.post(f"{BASE}/api/events", json={"sku_id": "agua_burst", "event_type": "retiro"})
        d = r.json()
        print(f"  Retiro {i+1}: {d['stock_before']} -> {d['stock_after']}")
        time.sleep(0.3)

    # 3. Predicciones
    print("\n=== GET /api/predictions ===")
    preds = requests.get(f"{BASE}/api/predictions").json()
    found_pred = False
    for p in preds:
        if p["minutes_remaining"] is not None:
            found_pred = True
            print(f"  {p['sku_name']}: {p['minutes_remaining']} min, "
                  f"rate={p['rate_per_hour']}/h, trend={p['trend']}, conf={p['confidence']}")
    if not found_pred:
        print("  (sin predicciones con datos suficientes)")

    assert any(p["rate_per_hour"] > 0 for p in preds), "FALLO: al menos 1 SKU debe tener rate > 0"
    print("  -> Predicciones OK")

    # 4. Heatmap
    print("\n=== GET /api/heatmap ===")
    hm = requests.get(f"{BASE}/api/heatmap").json()
    for s in hm.get("slots", []):
        print(f"  slot {s['slot_id']} ({s['sku_id']}): count={s['activity_count']}, intensity={s['intensity']}")

    assert len(hm.get("slots", [])) >= 2, "FALLO: al menos 2 slots con actividad"
    print("  -> Heatmap OK")

    # 5. Narrativas
    print("\n=== GET /api/narratives ===")
    narratives = requests.get(f"{BASE}/api/narratives").json()
    for n in narratives:
        print(f"  [{n['severity']:8s}] {n['icon']} {n['text']}")

    assert len(narratives) >= 3, f"FALLO: esperaba >= 3 narrativas, got {len(narratives)}"
    print("  -> Narrativas OK")

    # 6. Simular devolución
    print("\n=== Simulando devolución de nachos_naturasol ===")
    r = requests.post(f"{BASE}/api/events", json={"sku_id": "nachos_naturasol", "event_type": "devolucion"})
    d = r.json()
    print(f"  Devolución: {d['stock_before']} -> {d['stock_after']}")

    narratives2 = requests.get(f"{BASE}/api/narratives").json()
    devol_msgs = [n for n in narratives2 if "devuelto" in n["text"]]
    print(f"  Narrativas de devolución: {len(devol_msgs)}")

    print("\n" + "=" * 50)
    print("  INTEGRACIÓN P4 COMPLETA ✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
