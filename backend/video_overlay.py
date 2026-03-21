"""Video overlay — dibuja bounding boxes, semáforo y barra de estado sobre frames."""

import base64
import glob
import os

import cv2
import numpy as np

from contracts import SlotDetection


# Colores BGR según nivel de stock
_COLORS = {
    "ok": (0, 200, 0),         # verde
    "warning": (0, 200, 255),  # amarillo
    "critical": (0, 0, 220),   # rojo
}


class VideoOverlay:
    """Dibuja información visual sobre los frames del video."""

    # ------------------------------------------------------------------ #
    #  draw_overlay
    # ------------------------------------------------------------------ #
    def draw_overlay(self, frame: np.ndarray, detections: list[SlotDetection]) -> np.ndarray:
        """Dibuja bounding boxes con semáforo de stock sobre el frame."""
        overlay = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = _COLORS.get(det.stock_level, (200, 200, 200))

            # --- Bounding box ---
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)

            # --- Texto con fondo semitransparente ---
            label = f"{det.sku_name} x{det.count}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1
            (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            # Fondo semitransparente encima del box
            pad = 4
            txt_y1 = max(y1 - th - 2 * pad, 0)
            txt_y2 = y1
            txt_x2 = min(x1 + tw + 2 * pad, frame.shape[1])

            sub = overlay[txt_y1:txt_y2, x1:txt_x2]
            if sub.size > 0:
                rect_bg = np.full_like(sub, color, dtype=np.uint8)
                cv2.addWeighted(rect_bg, 0.55, sub, 0.45, 0, sub)

            cv2.putText(
                overlay,
                label,
                (x1 + pad, y1 - pad),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

            # --- Semáforo (círculo esquina superior derecha del box) ---
            radius = 8
            cx = x2 - radius - 4
            cy = y1 + radius + 4
            cv2.circle(overlay, (cx, cy), radius, color, -1)
            cv2.circle(overlay, (cx, cy), radius, (255, 255, 255), 1)

        return overlay

    # ------------------------------------------------------------------ #
    #  encode_frame
    # ------------------------------------------------------------------ #
    def encode_frame(self, frame: np.ndarray) -> str:
        """Codifica el frame a JPEG base64."""
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ok:
            raise RuntimeError("Error al codificar frame a JPEG")
        return base64.b64encode(buf.tobytes()).decode("ascii")

    # ------------------------------------------------------------------ #
    #  draw_status_bar
    # ------------------------------------------------------------------ #
    def draw_status_bar(self, frame: np.ndarray, inventory_summary: dict) -> np.ndarray:
        """Dibuja barra inferior con resumen de inventario.

        inventory_summary debe tener:
            stock_total   – unidades actuales
            stock_max     – capacidad máxima (ej. 56)
            alertas       – cantidad de alertas activas
        """
        h, w = frame.shape[:2]
        bar_h = 36
        result = np.vstack([frame, np.zeros((bar_h, w, 3), dtype=np.uint8)])

        stock_total = inventory_summary.get("stock_total", 0)
        stock_max = inventory_summary.get("stock_max", 56)
        alertas = inventory_summary.get("alertas", 0)

        text = f"Stock total: {stock_total}/{stock_max} | Alertas: {alertas}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(result, text, (10, h + 25), font, 0.65, (255, 255, 255), 1, cv2.LINE_AA)

        return result


# ====================================================================== #
#  Test manual
# ====================================================================== #
if __name__ == "__main__":
    # Buscar una imagen del dataset
    images_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "assets",
        "project-7-at-2026-03-20-21-09-0e2e8304",
        "images",
    )
    images = sorted(glob.glob(os.path.join(images_dir, "*.jpg")))
    if not images:
        print("ERROR: No se encontraron imágenes en", images_dir)
        raise SystemExit(1)

    frame = cv2.imread(images[0])
    if frame is None:
        print("ERROR: No se pudo leer la imagen", images[0])
        raise SystemExit(1)
    print(f"Imagen cargada: {images[0]}  ({frame.shape[1]}x{frame.shape[0]})")

    h, w = frame.shape[:2]

    # 3 detecciones ficticias con distintos niveles de stock
    fake_detections = [
        SlotDetection(
            sku_id="agua_burst",
            sku_name="Agua Burst",
            slot_id=1,
            bbox=(int(w * 0.05), int(h * 0.20), int(w * 0.30), int(h * 0.75)),
            confidence=0.93,
            count=7,
            stock_level="ok",  # >50 %
        ),
        SlotDetection(
            sku_id="nachos_naturasol",
            sku_name="Nachos Naturasol",
            slot_id=3,
            bbox=(int(w * 0.35), int(h * 0.20), int(w * 0.60), int(h * 0.75)),
            confidence=0.88,
            count=3,
            stock_level="warning",  # 25-50 %
        ),
        SlotDetection(
            sku_id="sisi_cola",
            sku_name="Sisi Cola",
            slot_id=5,
            bbox=(int(w * 0.65), int(h * 0.20), int(w * 0.90), int(h * 0.75)),
            confidence=0.85,
            count=1,
            stock_level="critical",  # <25 %
        ),
    ]

    overlay = VideoOverlay()

    # Dibujar overlay
    result = overlay.draw_overlay(frame, fake_detections)

    # Dibujar barra de estado
    result = overlay.draw_status_bar(
        result, {"stock_total": 11, "stock_max": 56, "alertas": 1}
    )

    # Guardar resultado
    out_path = os.path.join(os.path.dirname(__file__), "..", "test_overlay.jpg")
    cv2.imwrite(out_path, result)
    print(f"Imagen guardada: {os.path.abspath(out_path)}")

    # Verificar encode_frame
    b64 = overlay.encode_frame(result)
    print(f"Base64 size: {len(b64) / 1024:.1f} KB")
