"""
Motor de Detección — Módulo M2
Usa YOLOv8-seg para detectar productos del anaquel y generar eventos.
Hackathon Tiendas 3B
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from contracts import (
    EventType, DetectionEvent, SlotDetection, DetectionResult,
    AnnotatedFrame, InteractionEvent,
)

# --- Rutas ---
ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "best3.pt"

# --- Mapa de clases (debe coincidir con classes.txt y productosdelanaquel.md) ---
CLASS_NAMES = {
    0: ("agua_burst", "Agua Natural Burst 1500 ml"),
    1: ("burst_energetica_roja", "Bebida Energetica Red Burst 473 ml"),
    2: ("burst_energy", "Bebida Energetica Original Burst Energy 600 ml"),
    3: ("nachos_naturasol", "Nachos Con Sal Naturasol 200 gr"),
    4: ("nebraska_mango", "Bebida Mango-Durazno Nebraska 460 ml"),
    5: ("sisi_cola", "Refresco Cola Sin Azucar Sisi 355 ml"),
    6: ("sun_paradise_naranja", "Bebida Naranja Sun Paradise 900 ml"),
}

# Metadata de productos (de productosdelanaquel.md / Hackaton-datos_productos.csv)
PRODUCT_META = {
    "agua_burst":           {"src_product_id": 7746,  "barcode": 7502261250185, "presentation": "1500 ml", "line_name": "Agua Natural",           "group_name": "Water",      "iventa": 6},
    "burst_energetica_roja": {"src_product_id": 11024, "barcode": 7502261254411, "presentation": "473 ml",  "line_name": "Energetica Isotonica",   "group_name": "Beverages",  "iventa": 1},
    "burst_energy":         {"src_product_id": 22013, "barcode": 7502261273047, "presentation": "600 ml",  "line_name": "Energetica Isotonica",   "group_name": "Beverages",  "iventa": 12.5},
    "nachos_naturasol":     {"src_product_id": 25996, "barcode": 7503052023278, "presentation": "200 gr",  "line_name": "Frituras",               "group_name": "Snacks",     "iventa": 22},
    "nebraska_mango":       {"src_product_id": 26449, "barcode": 7502261273504, "presentation": "460 ml",  "line_name": "Jugos y Bebidas",        "group_name": "Beverages",  "iventa": 14},
    "sisi_cola":            {"src_product_id": 22287, "barcode": 7502261272415, "presentation": "355 ml",  "line_name": "Refrescos",              "group_name": "Beverages",  "iventa": 11},
    "sun_paradise_naranja": {"src_product_id": 24338, "barcode": 7502261269576, "presentation": "900 ml",  "line_name": "Jugos y Bebidas",        "group_name": "Beverages",  "iventa": 18},
}

STOCK_INITIAL = 8  # Unidades iniciales por SKU


# --- Carpeta de frames de debug ---
DEBUG_FRAMES_DIR = ROOT / "backend" / "debug_frames"

# Colores BGR según nivel de stock (para debug frames)
_STOCK_COLORS = {
    "ok": (0, 200, 0),
    "warning": (0, 200, 255),
    "critical": (0, 0, 220),
}


# --- Motor de detección ---
class DetectionEngine:
    def __init__(self, model_path: str | Path = MODEL_PATH, conf: float = 0.1,
                 save_frames: bool = False, imgsz: int = 640):
        self.model = YOLO(str(model_path))
        self.conf = conf
        self.imgsz = imgsz
        self.save_frames = save_frames
        self._frame_counter = 0
        # Preparar carpeta de debug frames
        if self.save_frames:
            DEBUG_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
        # Anti-flicker: historial de diferencias por sku para validación de 3 frames
        self._diff_history: dict[str, list[int]] = defaultdict(list)
        # Cooldown por slot (timestamp del último evento emitido)
        self._cooldown: dict[int, float] = {}
        self.cooldown_seconds = 3.0
        self.consistency_frames = 3
        # Warm-up: 3 inferences dummy
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        for _ in range(3):
            self.model.predict(dummy, conf=self.conf, imgsz=self.imgsz, verbose=False)
        print(f"DetectionEngine inicializado (conf={self.conf}, imgsz={self.imgsz}).")

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Ejecuta inferencia sobre un frame y retorna conteos por clase."""
        import time

        results = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)
        counts: dict[str, int] = {info[0]: 0 for info in CLASS_NAMES.values()}
        raw_detections: list[tuple[str, str, int, tuple, float]] = []

        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                conf = float(boxes.conf[i].item())
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                bbox = (int(x1), int(y1), int(x2), int(y2))

                if cls_id in CLASS_NAMES:
                    sku_id, sku_name = CLASS_NAMES[cls_id]
                    counts[sku_id] += 1
                    raw_detections.append((sku_id, sku_name, cls_id, bbox, conf))

        # Segunda pasada: asignar stock_level basado en conteo total por SKU
        all_detections: list[SlotDetection] = []
        for sku_id, sku_name, cls_id, bbox, conf in raw_detections:
            total = counts[sku_id]
            pct = total / STOCK_INITIAL
            if pct > 0.50:
                stock_level = "ok"
            elif pct > 0.25:
                stock_level = "warning"
            else:
                stock_level = "critical"

            all_detections.append(SlotDetection(
                sku_id=sku_id,
                sku_name=sku_name,
                slot_id=cls_id + 1,
                bbox=bbox,
                confidence=conf,
                count=total,
                stock_level=stock_level,
            ))

        det_result = DetectionResult(
            timestamp=time.time(),
            counts=counts,
            detections=all_detections,
        )

        # --- Guardar debug frame anotado ---
        if self.save_frames:
            self._save_debug_frame(frame, all_detections)

        return det_result

    def _save_debug_frame(self, frame: np.ndarray, detections: list[SlotDetection]):
        """Guarda un frame anotado con bounding boxes en debug_frames/."""
        self._frame_counter += 1
        annotated = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = _STOCK_COLORS.get(det.stock_level, (200, 200, 200))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{det.sku_name} x{det.count} ({det.confidence:.2f})"
            cv2.putText(annotated, label, (x1, max(y1 - 8, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        total = sum(1 for _ in detections)
        info = f"Frame #{self._frame_counter} | conf={self.conf} | detecciones={total}"
        cv2.putText(annotated, info, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = DEBUG_FRAMES_DIR / f"frame_{self._frame_counter:04d}_{ts}.jpg"
        cv2.imwrite(str(path), annotated)

    def compare(
        self, prev: DetectionResult, curr: DetectionResult
    ) -> list[DetectionEvent]:
        """Compara dos DetectionResult y genera eventos si hay cambios consistentes."""
        import time

        events: list[DetectionEvent] = []
        now = datetime.now()

        for sku_id in curr.counts:
            prev_count = prev.counts.get(sku_id, 0)
            curr_count = curr.counts.get(sku_id, 0)
            diff = curr_count - prev_count

            if diff == 0:
                # Sin cambio: limpiar historial de este sku
                self._diff_history[sku_id].clear()
                continue

            # Acumular diferencia para anti-flicker
            self._diff_history[sku_id].append(diff)

            # Solo emitir si el cambio es consistente por N frames
            history = self._diff_history[sku_id]
            if len(history) < self.consistency_frames:
                continue

            # Verificar que los últimos N diffs tienen el mismo signo
            recent = history[-self.consistency_frames :]
            if not all(d < 0 for d in recent) and not all(d > 0 for d in recent):
                continue

            consistent_diff = recent[-1]

            # Cooldown por slot
            slot_id = self._get_slot_for_sku(sku_id)
            last_event_time = self._cooldown.get(slot_id, 0)
            if time.time() - last_event_time < self.cooldown_seconds:
                continue

            # Determinar tipo de evento
            if consistent_diff < 0:
                event_type = EventType.RETIRO
            else:
                event_type = EventType.DEVOLUCION

            # Promediar confianza de TODAS las detecciones de este SKU
            bbox = (0, 0, 0, 0)
            conf_sum = 0.0
            conf_count = 0
            for det in curr.detections:
                if det.sku_id == sku_id:
                    if conf_count == 0:
                        bbox = det.bbox  # Tomar primer bbox como representativo
                    conf_sum += det.confidence
                    conf_count += 1
            avg_conf = conf_sum / conf_count if conf_count > 0 else 0.0

            sku_name = self._get_name_for_sku(sku_id)

            event = DetectionEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                sku_id=sku_id,
                sku_name=sku_name,
                slot_id=slot_id,
                confidence=avg_conf,
                timestamp=now,
                bbox=bbox,
                count_before=prev_count,
                count_after=curr_count,
            )
            events.append(event)

            # Registrar cooldown y limpiar historial
            self._cooldown[slot_id] = time.time()
            self._diff_history[sku_id].clear()

        return events

    @staticmethod
    def _get_slot_for_sku(sku_id: str) -> int:
        for cls_id, (sid, _) in CLASS_NAMES.items():
            if sid == sku_id:
                return cls_id + 1
        return 0

    @staticmethod
    def _get_name_for_sku(sku_id: str) -> str:
        for _, (sid, name) in CLASS_NAMES.items():
            if sid == sku_id:
                return name
        return sku_id


# --- Monitoreo en tiempo real ---
if __name__ == "__main__":
    import argparse
    import time as _time
    from camera_capture import CameraCapture

    parser = argparse.ArgumentParser(description="Monitoreo en tiempo real del anaquel")
    parser.add_argument("--conf", type=float, default=0.1,
                        help="Umbral de confianza (0.0-1.0)")
    parser.add_argument("--source", default=None,
                        help="Fuente de video (RTSP URL o int para USB)")
    args = parser.parse_args()

    print("=" * 60)
    print("  DetectionEngine — Monitoreo en tiempo real")
    print(f"  conf={args.conf}  |  Ctrl+C para detener")
    print("=" * 60)

    engine = DetectionEngine(conf=args.conf, save_frames=False)

    source = args.source
    if source is not None:
        try:
            source = int(source)
        except ValueError:
            pass
    cam = CameraCapture(source) if source is not None else CameraCapture()
    if not cam.start():
        print("ERROR: No se pudo conectar a la cámara")
        exit(1)

    prev_result = None
    event_count = 0

    print("\nEscuchando eventos en tiempo real...\n")

    try:
        while True:
            for fd in cam.get_frames():
                result = engine.detect(fd.frame)

                if prev_result is not None:
                    events = engine.compare(prev_result, result)
                    for ev in events:
                        event_count += 1
                        ts = ev.timestamp.strftime('%H:%M:%S')
                        print(f"  ⚡ [{ts}] {ev.event_type.value.upper()}: "
                              f"{ev.sku_name} ({ev.count_before}→{ev.count_after}) "
                              f"conf={ev.confidence:.2f}")

                prev_result = result

            # Si get_frames termina (desconexión), reconectar
            print("[!] Cámara desconectada, reconectando...")
            cam.stop()
            _time.sleep(2)
            if not cam.start():
                print("ERROR: No se pudo reconectar")
                break

    except KeyboardInterrupt:
        print("\n\nDetenido por el usuario.")
    finally:
        cam.stop()
        print(f"Total eventos detectados: {event_count}")
