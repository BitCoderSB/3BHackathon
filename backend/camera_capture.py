"""Captura de cámara — RTSP con reconexión y fallback USB."""

import time
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class FrameData:
    frame: np.ndarray          # Imagen BGR, shape (H, W, 3), dtype uint8
    timestamp: float           # time.time() al momento de captura
    frame_id: int              # Secuencial incremental
    resolution: tuple[int, int]  # (width, height)


# URLs RTSP por defecto (de assets/cadenadeconexion.md)
DEFAULT_RTSP = "rtsp://admin:admin1234@172.31.13.190:554/cam/realmonitor?channel=1&subtype=0"

MAX_RECONNECT = 5
RECONNECT_DELAY = 3  # segundos


class CameraCapture:
    """Captura frames de cámara RTSP o USB con reconexión automática."""

    def __init__(self, source=DEFAULT_RTSP):
        """source: str RTSP URL o int para cámara USB."""
        self._source = source
        self._cap: cv2.VideoCapture | None = None
        self._frame_id = 0

    # ------------------------------------------------------------------ #
    #  start / stop
    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        """Abre la fuente de video. Retorna True si tuvo éxito."""
        self._cap = cv2.VideoCapture(self._source)
        if self._cap.isOpened():
            print(f"[CameraCapture] Conectado a {self._source}")
            return True

        # Reconexión RTSP
        if isinstance(self._source, str):
            for attempt in range(1, MAX_RECONNECT + 1):
                print(f"[CameraCapture] Reintento RTSP {attempt}/{MAX_RECONNECT}...")
                time.sleep(RECONNECT_DELAY)
                self._cap = cv2.VideoCapture(self._source)
                if self._cap.isOpened():
                    print(f"[CameraCapture] Conectado a {self._source} (intento {attempt})")
                    return True

            # Fallback a USB
            print("[CameraCapture] RTSP falló. Intentando cámara USB 0...")
            self._source = 0
            self._cap = cv2.VideoCapture(0)
            if self._cap.isOpened():
                print("[CameraCapture] Conectado a cámara USB 0")
                return True

        print("[CameraCapture] ERROR: No se pudo abrir ninguna fuente de video")
        return False

    def stop(self):
        """Libera la cámara."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        print("[CameraCapture] Cámara liberada")

    # ------------------------------------------------------------------ #
    #  get_frames  (generador)
    # ------------------------------------------------------------------ #
    def get_frames(self):
        """Yield FrameData continuo desde la cámara."""
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("Cámara no iniciada. Llama a start() primero.")

        while self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret:
                # Intentar reconectar
                if not self._reconnect():
                    break
                continue

            self._frame_id += 1
            h, w = frame.shape[:2]
            yield FrameData(
                frame=frame,
                timestamp=time.time(),
                frame_id=self._frame_id,
                resolution=(w, h),
            )

    # ------------------------------------------------------------------ #
    #  reconexión interna
    # ------------------------------------------------------------------ #
    def _reconnect(self) -> bool:
        """Intenta reconectar a la fuente actual."""
        print("[CameraCapture] Conexión perdida. Reintentando...")
        for attempt in range(1, MAX_RECONNECT + 1):
            time.sleep(RECONNECT_DELAY)
            self._cap = cv2.VideoCapture(self._source)
            if self._cap.isOpened():
                print(f"[CameraCapture] Reconectado (intento {attempt})")
                return True

        # Fallback USB si la fuente era RTSP
        if isinstance(self._source, str):
            print("[CameraCapture] Fallback a USB 0...")
            self._source = 0
            self._cap = cv2.VideoCapture(0)
            if self._cap.isOpened():
                print("[CameraCapture] Conectado a cámara USB 0")
                return True

        print("[CameraCapture] No se pudo reconectar")
        return False

    # ------------------------------------------------------------------ #
    #  stream_loop
    # ------------------------------------------------------------------ #
    def stream_loop(self, detection_engine, overlay, callback, max_fps=5):
        """Loop de streaming con detección, overlay y callback.

        Args:
            detection_engine: objeto con .detect(frame) o None (modo sin CV)
            overlay: VideoOverlay con .draw_overlay() y .encode_frame()
            callback: función(frame_base64, detections) llamada por frame
            max_fps: máximo de frames procesados por segundo (default 5)
        """
        min_interval = 1.0 / max_fps
        last_time = 0.0

        for fd in self.get_frames():
            now = time.time()
            if now - last_time < min_interval:
                continue  # skip frame para respetar max_fps
            last_time = now

            detections = []
            detection_result = None
            if detection_engine is not None:
                detection_result = detection_engine.detect(fd.frame)
                detections = detection_result.detections

            if overlay is not None:
                drawn = overlay.draw_overlay(fd.frame, detections)
                frame_b64 = overlay.encode_frame(drawn)
            else:
                frame_b64 = None

            # callback decide qué hacer (enviar al API, imprimir, etc.)
            should_stop = callback(frame_b64, detection_result if detection_result else detections)
            if should_stop:
                break


# ====================================================================== #
#  Test manual — Fase 2.3 (stream_loop sin CV, 20 frames, max 5 FPS)
# ====================================================================== #
if __name__ == "__main__":
    from video_overlay import VideoOverlay

    cam = CameraCapture()  # RTSP por defecto, fallback a USB
    if not cam.start():
        raise SystemExit(1)

    overlay = VideoOverlay()
    state = {"count": 0}
    t_start = time.time()

    def on_frame(frame_b64, detections):
        state["count"] += 1
        size_kb = len(frame_b64) / 1024 if frame_b64 else 0
        print(f"Frame {state['count']}: {size_kb:.1f} KB base64")
        return state["count"] >= 20  # detenerse a los 20 frames

    try:
        cam.stream_loop(
            detection_engine=None,
            overlay=overlay,
            callback=on_frame,
            max_fps=5,
        )
    finally:
        elapsed = time.time() - t_start
        actual_fps = state["count"] / elapsed if elapsed > 0 else 0
        print(f"\n{state['count']} frames en {elapsed:.1f}s — {actual_fps:.1f} FPS efectivos")
        cam.stop()
