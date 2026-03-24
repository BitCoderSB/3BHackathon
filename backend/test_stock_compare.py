"""
Comparador de stock — productosdelanaquel.md vs detección en tiempo real.

Captura un frame de la cámara, detecta productos y compara con el inventario
esperado según productosdelanaquel.md (8 unidades iniciales por SKU).

Uso:
    python test_stock_compare.py              # conf=0.25 (detecta más)
    python test_stock_compare.py --conf 0.5   # conf más alto (detecta menos)
"""

import argparse
import os
import time

import cv2
import numpy as np

from detection_engine import DetectionEngine, CLASS_NAMES, STOCK_INITIAL, PRODUCT_META
from video_overlay import VideoOverlay
from camera_capture import CameraCapture

# Colores ANSI para la consola
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def color_bar(current, total, width=20):
    """Genera barra visual con color según porcentaje."""
    pct = current / total if total > 0 else 0
    filled = int(pct * width)
    empty = width - filled

    if pct > 0.50:
        color = GREEN
    elif pct > 0.25:
        color = YELLOW
    else:
        color = RED

    bar = color + "█" * filled + DIM + "░" * empty + RESET
    return bar


def main():
    parser = argparse.ArgumentParser(description="Comparador stock vs detección")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="Umbral de confianza (default 0.25)")
    parser.add_argument("--frames", type=int, default=5,
                        help="Frames a promediar para estabilizar conteos")
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*70}")
    print(f"   COMPARADOR: Stock del Anaquel vs Detección por Cámara")
    print(f"{'='*70}{RESET}\n")
    print(f"  Confianza: {args.conf}   Frames a promediar: {args.frames}\n")

    # --- Cargar motor ---
    print("Cargando DetectionEngine...")
    engine = DetectionEngine(conf=args.conf)

    print("Conectando cámara...")
    cam = CameraCapture()
    if not cam.start():
        print(f"{RED}ERROR: No se pudo conectar a la cámara{RESET}")
        raise SystemExit(1)

    # --- Capturar N frames y acumular conteos ---
    print(f"Capturando {args.frames} frames para promediar...\n")
    accumulated = {info[0]: [] for info in CLASS_NAMES.values()}

    count = 0
    for fd in cam.get_frames():
        result = engine.detect(fd.frame)
        for sku_id, cnt in result.counts.items():
            accumulated[sku_id].append(cnt)
        count += 1
        print(f"  Frame {count}/{args.frames} capturado")
        if count >= args.frames:
            break
        time.sleep(0.3)

    cam.stop()

    # --- Calcular promedio y moda ---
    from statistics import mode, StatisticsError

    detected = {}
    for sku_id, counts_list in accumulated.items():
        if counts_list:
            # Usar moda (valor más frecuente) para evitar outliers
            try:
                detected[sku_id] = mode(counts_list)
            except StatisticsError:
                detected[sku_id] = round(sum(counts_list) / len(counts_list))
        else:
            detected[sku_id] = 0

    # --- Guardar frame anotado ---
    overlay = VideoOverlay()
    # Reconectar para un frame final
    cam2 = CameraCapture()
    if cam2.start():
        for fd in cam2.get_frames():
            last_result = engine.detect(fd.frame)
            annotated = overlay.draw_overlay(fd.frame, last_result.detections)

            info_text = f"conf={args.conf} | Detectados: {sum(last_result.counts.values())}"
            cv2.putText(annotated, info_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)

            out_dir = os.path.join(os.path.dirname(__file__), "debug_frames")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "stock_compare_frame.jpg")
            cv2.imwrite(out_path, annotated)
            print(f"\n  Frame guardado: {out_path}")
            break
        cam2.stop()

    # --- Tabla de comparación ---
    print(f"\n{BOLD}{'='*70}")
    print(f"   RESULTADO: Stock Esperado vs Detectado")
    print(f"{'='*70}{RESET}\n")

    header = f"  {'Producto':<42} {'Esperado':>8} {'Detectado':>9} {'Diff':>5}  {'Stock'}"
    print(f"{BOLD}{header}{RESET}")
    print(f"  {'─'*42} {'─'*8} {'─'*9} {'─'*5}  {'─'*22}")

    total_expected = 0
    total_detected = 0
    missing_products = []

    for cls_id in sorted(CLASS_NAMES.keys()):
        sku_id, sku_name = CLASS_NAMES[cls_id]
        meta = PRODUCT_META.get(sku_id, {})
        expected = STOCK_INITIAL
        det = detected.get(sku_id, 0)
        diff = det - expected

        total_expected += expected
        total_detected += det

        bar = color_bar(det, expected)

        # Color de la diferencia
        if diff == 0:
            diff_str = f"{GREEN}  0{RESET}"
        elif diff < 0:
            diff_str = f"{RED}{diff:>+3}{RESET}"
        else:
            diff_str = f"{YELLOW}{diff:>+3}{RESET}"

        # Nombre con presentación
        display_name = f"{sku_name}"

        # Indicador si no detecta nada
        alert = ""
        if det == 0:
            alert = f" {RED}⚠ NO DETECTADO{RESET}"
            missing_products.append(sku_name)

        print(f"  {display_name:<42} {expected:>8} {det:>9} {diff_str}  {bar} {det}/{expected}{alert}")

    print(f"  {'─'*42} {'─'*8} {'─'*9} {'─'*5}  {'─'*22}")
    pct = total_detected / total_expected * 100 if total_expected > 0 else 0
    total_bar = color_bar(total_detected, total_expected)
    print(f"  {'TOTAL':<42} {total_expected:>8} {total_detected:>9} {total_detected-total_expected:>+5}  {total_bar} {total_detected}/{total_expected} ({pct:.0f}%)")

    # --- Resumen ---
    print(f"\n{BOLD}{'='*70}")
    print(f"   ANÁLISIS")
    print(f"{'='*70}{RESET}\n")

    print(f"  Productos en anaquel (productosdelanaquel.md): {BOLD}7{RESET}")
    print(f"  Stock inicial esperado por producto:           {BOLD}{STOCK_INITIAL}{RESET}")
    print(f"  Total esperado (7 × {STOCK_INITIAL}):                       {BOLD}{total_expected}{RESET}")
    print(f"  Total detectado con conf={args.conf}:              {BOLD}{total_detected}{RESET}")
    print(f"  Cobertura de detección:                        {BOLD}{pct:.1f}%{RESET}")

    if missing_products:
        print(f"\n  {RED}{BOLD}Productos NO detectados:{RESET}")
        for name in missing_products:
            print(f"    {RED}✗ {name}{RESET}")

    under_detected = []
    for cls_id in sorted(CLASS_NAMES.keys()):
        sku_id, sku_name = CLASS_NAMES[cls_id]
        det = detected.get(sku_id, 0)
        if 0 < det < STOCK_INITIAL:
            under_detected.append((sku_name, det, STOCK_INITIAL))

    if under_detected:
        print(f"\n  {YELLOW}{BOLD}Productos sub-detectados (detecta menos de {STOCK_INITIAL}):{RESET}")
        for name, det, exp in under_detected:
            print(f"    {YELLOW}△ {name}: detecta {det}/{exp}{RESET}")

    print(f"\n  {CYAN}Nota: Si faltan productos, considerar:{RESET}")
    print(f"    1. Bajar --conf (ej: --conf 0.15) para captar más")
    print(f"    2. Re-entrenar el modelo con más datos del ángulo actual")
    print(f"    3. Verificar que los productos estén a la vista de la cámara\n")


if __name__ == "__main__":
    main()
