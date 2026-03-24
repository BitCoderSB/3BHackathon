"""
Test visual — Guarda frames anotados con bounding boxes para inspección.
Captura N frames de la cámara, ejecuta detección y guarda las imágenes
en backend/debug_frames/ para que puedas ver qué detecta el modelo.

Uso:
    python test_visual_detection.py              # conf=0.5 (default)
    python test_visual_detection.py --conf 0.3   # umbral más bajo, detecta más
    python test_visual_detection.py --conf 0.2 --frames 10
"""

import argparse
import os
import time

import cv2
import numpy as np

from detection_engine import DetectionEngine, CLASS_NAMES, STOCK_INITIAL
from video_overlay import VideoOverlay
from camera_capture import CameraCapture

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "debug_frames")


def main():
    parser = argparse.ArgumentParser(description="Test visual de detección")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Umbral de confianza (0.0-1.0). Más bajo = detecta más")
    parser.add_argument("--frames", type=int, default=5,
                        help="Cantidad de frames a guardar")
    parser.add_argument("--source", default=None,
                        help="Fuente de video (RTSP URL, int para USB, o ruta a imagen/video)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Inicializar ---
    print(f"=== Test Visual de Detección ===")
    print(f"    conf={args.conf}  frames={args.frames}")
    print()

    engine = DetectionEngine(conf=args.conf)
    overlay = VideoOverlay()

    # Modo imagen estática (para probar con una foto del dataset)
    if args.source and os.path.isfile(args.source):
        print(f"Procesando imagen: {args.source}")
        frame = cv2.imread(args.source)
        if frame is None:
            print(f"ERROR: No se pudo leer {args.source}")
            return
        _process_and_save(engine, overlay, frame, 1, args.conf)
        print(f"\nImágenes guardadas en: {os.path.abspath(OUTPUT_DIR)}")
        return

    # Modo cámara
    source = args.source
    if source is not None:
        try:
            source = int(source)
        except ValueError:
            pass
    cam = CameraCapture(source) if source is not None else CameraCapture()
    if not cam.start():
        raise SystemExit(1)

    saved = 0
    try:
        for fd in cam.get_frames():
            saved += 1
            _process_and_save(engine, overlay, fd.frame, saved, args.conf)
            if saved >= args.frames:
                break
            time.sleep(0.5)  # pequeña pausa entre capturas
    finally:
        cam.stop()

    print(f"\n{'='*60}")
    print(f"{saved} frames guardados en: {os.path.abspath(OUTPUT_DIR)}")
    print(f"{'='*60}")


def _process_and_save(engine, overlay, frame, idx, conf):
    """Detecta, anota y guarda un frame."""
    result = engine.detect(frame)

    # --- Imprimir conteos ---
    total = sum(result.counts.values())
    print(f"\n--- Frame {idx} ({frame.shape[1]}x{frame.shape[0]}) ---")
    print(f"Total detecciones: {total}")
    for sku_id, count in sorted(result.counts.items()):
        if count > 0:
            print(f"  {sku_id}: {count}")

    # Detalle por detección individual
    if result.detections:
        print(f"\nDetalle ({len(result.detections)} objetos):")
        for det in result.detections:
            print(f"  {det.sku_name} | conf={det.confidence:.2f} | "
                  f"bbox={det.bbox} | nivel={det.stock_level}")

    # --- Dibujar overlay ---
    annotated = overlay.draw_overlay(frame, result.detections)

    # Agregar texto con resumen en la parte superior
    info_text = f"conf={conf} | Detectados: {total}"
    cv2.putText(annotated, info_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)

    # Dibujar barra de estado
    stock_total = sum(result.counts.values())
    stock_max = len(CLASS_NAMES) * STOCK_INITIAL
    annotated = overlay.draw_status_bar(
        annotated,
        {"stock_total": stock_total, "stock_max": stock_max, "alertas": 0},
    )

    # --- Guardar ---
    # Frame original (sin anotaciones)
    raw_path = os.path.join(OUTPUT_DIR, f"frame_{idx:02d}_raw.jpg")
    cv2.imwrite(raw_path, frame)

    # Frame anotado (con bounding boxes)
    ann_path = os.path.join(OUTPUT_DIR, f"frame_{idx:02d}_detected.jpg")
    cv2.imwrite(ann_path, annotated)

    print(f"  → Guardado: {raw_path}")
    print(f"  → Guardado: {ann_path}")


if __name__ == "__main__":
    main()
