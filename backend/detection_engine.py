"""
Motor de Detección — Módulo M2
Usa YOLOv8-seg para detectar productos del anaquel y generar eventos.
Hackathon Tiendas 3B
"""
from __future__ import annotations

import glob
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# --- Rutas ---
ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "best.pt"

# --- Mapa de clases (debe coincidir con classes.txt) ---
CLASS_NAMES = {
    0: ("agua_burst", "Agua Natural Burst 1500ml"),
    1: ("burst_energetica_roja", "Bebida Energetica Red Burst 473ml"),
    2: ("burst_energy", "Bebida Energetica Original Burst Energy 600ml"),
    3: ("nachos_naturasol", "Nachos Con Sal Naturasol 200gr"),
    4: ("nebraska_mango", "Bebida Mango-Durazno Nebraska 460ml"),
    5: ("sisi_cola", "Refresco Cola Sin Azucar Sisi 355ml"),
    6: ("sun_paradise_naranja", "Bebida Naranja Sun Paradise 900ml"),
}

STOCK_INITIAL = 8  # Unidades iniciales por SKU


# --- Contratos (C2, C3) ---
class EventType(Enum):
    RETIRO = "retiro"
    DEVOLUCION = "devolucion"


@dataclass
class DetectionEvent:
    event_id: str
    event_type: EventType
    sku_id: str
    sku_name: str
    slot_id: int
    confidence: float
    timestamp: datetime
    bbox: tuple[int, int, int, int]
    count_before: int
    count_after: int


@dataclass
class SlotDetection:
    sku_id: str
    sku_name: str
    slot_id: int
    bbox: tuple[int, int, int, int]
    confidence: float
    count: int
    stock_level: str  # "ok" | "warning" | "critical"


@dataclass
class DetectionResult:
    timestamp: float
    counts: dict[str, int]  # sku_id -> cantidad detectada
    detections: list[SlotDetection] = field(default_factory=list)


@dataclass
class AnnotatedFrame:
    frame: np.ndarray
    timestamp: float
    detections: list[SlotDetection]


@dataclass
class InteractionEvent:
    slot_id: int
    sku_id: str
    region: tuple[int, int, int, int]
    timestamp: datetime
    interaction_type: str  # "hand_detected" | "product_moved"


# --- Motor de detección ---
class DetectionEngine:
    def __init__(self, model_path: str | Path = MODEL_PATH, conf: float = 0.5):
        self.model = YOLO(str(model_path))
        self.conf = conf
        # Anti-flicker: historial de diferencias por sku para validación de 3 frames
        self._diff_history: dict[str, list[int]] = defaultdict(list)
        # Cooldown por slot (timestamp del último evento emitido)
        self._cooldown: dict[int, float] = {}
        self.cooldown_seconds = 3.0
        self.consistency_frames = 3
        # Warm-up: 3 inferences dummy
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        for _ in range(3):
            self.model.predict(dummy, conf=self.conf, verbose=False)
        print("DetectionEngine inicializado y warm-up completado.")

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Ejecuta inferencia sobre un frame y retorna conteos por clase."""
        import time

        results = self.model.predict(frame, conf=self.conf, verbose=False)
        counts: dict[str, int] = {info[0]: 0 for info in CLASS_NAMES.values()}
        all_detections: list[SlotDetection] = []

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
                    count = counts[sku_id]

                    pct = count / STOCK_INITIAL
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
                        count=count,
                        stock_level=stock_level,
                    ))

        return DetectionResult(
            timestamp=time.time(),
            counts=counts,
            detections=all_detections,
        )

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

            # Buscar bbox representativo de este sku en detecciones actuales
            bbox = (0, 0, 0, 0)
            avg_conf = 0.0
            for det in curr.detections:
                if det.sku_id == sku_id:
                    bbox = det.bbox
                    avg_conf = det.confidence
                    break

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


# --- Test ---
if __name__ == "__main__":
    # Buscar una imagen del dataset para prueba
    images_dir = ROOT / "assets" / "project-7-at-2026-03-20-21-09-0e2e8304" / "images"
    images = sorted(glob.glob(str(images_dir / "*.jpg")))

    if not images:
        print("ERROR: No se encontraron imágenes en", images_dir)
        exit(1)

    test_img_path = images[0]
    print(f"Imagen de prueba: {test_img_path}")

    # Cargar modelo
    engine = DetectionEngine()

    # Leer imagen
    frame = cv2.imread(test_img_path)
    if frame is None:
        print(f"ERROR: No se pudo leer {test_img_path}")
        exit(1)

    print(f"Frame shape: {frame.shape}")

    # Detectar
    result = engine.detect(frame)

    print("\n=== Conteos detectados ===")
    for sku_id, count in sorted(result.counts.items()):
        print(f"  {sku_id}: {count}")

    print(f"\nTotal detecciones: {len(result.detections)}")
    for det in result.detections:
        print(f"  {det.sku_name} (slot {det.slot_id}): conf={det.confidence:.2f}, "
              f"bbox={det.bbox}, nivel={det.stock_level}")

    # Simular compare con un segundo frame (misma imagen → sin cambios)
    result2 = engine.detect(frame)
    events = engine.compare(result, result2)
    print(f"\nEventos generados (mismo frame): {len(events)} (esperado: 0)")

    print("\n✅ DetectionEngine funcional.")
