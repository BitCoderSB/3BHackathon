"""Captura de cámara — RTSP con reconexión, fallback USB y flush de buffer."""

import threading
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
DEFAULT_RTSP = "rtsp://admin:admin1234@172.31.13.191:554/cam/realmonitor?channel=1&subtype=0"

MAX_RECONNECT = 5
RECONNECT_DELAY = 2  # segundos


class CameraCapture:
    """Captura frames de cámara RTSP o USB con reconexión automática.
    
    Usa un hilo lector que siempre consume el frame más reciente del buffer
    RTSP, eliminando lag por frames acumulados.
    """

    def __init__(self, source=DEFAULT_RTSP):
        """source: str RTSP URL o int para cámara USB."""
        self._source = source
        self._original_source = source  # Guardar para re-intentos
        self._cap: cv2.VideoCapture | None = None
        self._frame_id = 0
        self._stopped = False
        # Hilo lector: siempre lee el último frame para evitar lag RTSP
        self._grab_thread: threading.Thread | None = None
        self._latest_frame: np.ndarray | None = None
        self._frame_lock = threading.Lock()
        self._frame_ready = threading.Event()
        self._consecutive_failures = 0

    # ------------------------------------------------------------------ #
    #  start / stop
    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        """Abre la fuente de video. Retorna True si tuvo éxito."""
        self._stopped = False
        self._cap = self._open_capture(self._source)
        if self._cap and self._cap.isOpened():
            print(f"[CameraCapture] Conectado a {self._source}")
            self._start_grab_thread()
            return True

        # Reconexión RTSP
        if isinstance(self._source, str):
            for attempt in range(1, MAX_RECONNECT + 1):
                print(f"[CameraCapture] Reintento RTSP {attempt}/{MAX_RECONNECT}...")
                time.sleep(RECONNECT_DELAY)
                self._cap = self._open_capture(self._source)
                if self._cap and self._cap.isOpened():
                    print(f"[CameraCapture] Conectado a {self._source} (intento {attempt})")
                    self._start_grab_thread()
                    return True

            # Fallback a USB
            print("[CameraCapture] RTSP falló. Intentando cámara USB 0...")
            self._source = 0
            self._cap = self._open_capture(0)
            if self._cap and self._cap.isOpened():
                print("[CameraCapture] Conectado a cámara USB 0")
                self._start_grab_thread()
                return True

        print("[CameraCapture] ERROR: No se pudo abrir ninguna fuente de video")
        return False

    def _open_capture(self, source) -> cv2.VideoCapture:
        """Abre VideoCapture con configuración optimizada para baja latencia."""
        if isinstance(source, str):
            # RTSP: usar FFMPEG con TCP para mayor estabilidad
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        else:
            cap = cv2.VideoCapture(source)
        
        if cap.isOpened():
            # Buffer mínimo para reducir lag
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Timeouts para RTSP 
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        return cap

    def _start_grab_thread(self):
        """Inicia hilo que lee frames continuamente (flush del buffer RTSP)."""
        if self._grab_thread and self._grab_thread.is_alive():
            return
        self._grab_thread = threading.Thread(target=self._grab_loop, daemon=True)
        self._grab_thread.start()

    def _grab_loop(self):
        """Lee frames en loop constantemente, guardando solo el más reciente."""
        while not self._stopped and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret:
                self._consecutive_failures += 1
                if self._consecutive_failures > 30:
                    print("[CameraCapture] Demasiados fallos consecutivos en grab_loop")
                    break
                time.sleep(0.05)
                continue
            self._consecutive_failures = 0
            with self._frame_lock:
                self._latest_frame = frame
            self._frame_ready.set()
        print("[CameraCapture] grab_loop terminado")

    def stop(self):
        """Libera la cámara y detiene el hilo lector."""
        self._stopped = True
        if self._grab_thread and self._grab_thread.is_alive():
            self._grab_thread.join(timeout=3)
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._latest_frame = None
        self._frame_ready.clear()
        print("[CameraCapture] Cámara liberada")

    # ------------------------------------------------------------------ #
    #  get_frames  (generador) — usa frame más reciente del hilo lector
    # ------------------------------------------------------------------ #
    def get_frames(self):
        """Yield FrameData continuo desde la cámara (siempre el frame más reciente)."""
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("Cámara no iniciada. Llama a start() primero.")

        while not self._stopped:
            # Esperar hasta que haya un frame disponible (max 2s)
            if not self._frame_ready.wait(timeout=2.0):
                # Sin frames por 2s — verificar si la conexión sigue viva
                if not self._cap or not self._cap.isOpened():
                    if not self._reconnect():
                        break
                continue

            with self._frame_lock:
                frame = self._latest_frame
                self._latest_frame = None
            self._frame_ready.clear()

            if frame is None:
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
        """Intenta reconectar a la fuente actual (o RTSP original)."""
        print("[CameraCapture] Conexión perdida. Reintentando...")
        # Detener hilo lector anterior
        self._stopped = True
        if self._grab_thread and self._grab_thread.is_alive():
            self._grab_thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        self._stopped = False

        # Intentar reconectar primero a la fuente original (RTSP)
        sources_to_try = [self._original_source]
        if isinstance(self._original_source, str):
            sources_to_try.append(0)  # Fallback USB

        for source in sources_to_try:
            for attempt in range(1, MAX_RECONNECT + 1):
                time.sleep(RECONNECT_DELAY)
                self._cap = self._open_capture(source)
                if self._cap and self._cap.isOpened():
                    self._source = source
                    print(f"[CameraCapture] Reconectado a {source} (intento {attempt})")
                    self._start_grab_thread()
                    return True

        print("[CameraCapture] No se pudo reconectar")
        return False

    # ------------------------------------------------------------------ #
    #  stream_loop
    # ------------------------------------------------------------------ #
    def stream_loop(self, detection_engine, overlay, callback, max_fps=5,
                     stream_width=640, detect_every=2):
        """Loop de streaming con detección, overlay y callback.

        Args:
            detection_engine: objeto con .detect(frame) y .compare() o None
            overlay: VideoOverlay con .draw_overlay() y .encode_frame()
            callback: función(frame_base64, detection_result, events)
                      Retorna True para detener el loop.
            max_fps: máximo de frames procesados por segundo (default 5)
            stream_width: ancho máximo para redimensionar antes de procesar
            detect_every: ejecutar detección cada N frames (1=todos, 2=alternados)
        """
        min_interval = 1.0 / max_fps
        last_time = 0.0
        prev_result = None
        frame_count = 0

        for fd in self.get_frames():
            now = time.time()
            if now - last_time < min_interval:
                continue  # skip frame para respetar max_fps
            last_time = now
            frame_count += 1

            frame = fd.frame
            # Redimensionar para reducir carga de detección y tamaño de payload
            h, w = frame.shape[:2]
            if w > stream_width:
                scale = stream_width / w
                frame = cv2.resize(frame, (stream_width, int(h * scale)),
                                   interpolation=cv2.INTER_AREA)

            detection_result = None
            slot_detections = []
            events = []

            # Ejecutar detección solo cada N frames para reducir carga
            run_detection = detection_engine is not None and (frame_count % detect_every == 0)
            if run_detection:
                detection_result = detection_engine.detect(frame)
                slot_detections = detection_result.detections

                if prev_result is not None:
                    events = detection_engine.compare(prev_result, detection_result)
                prev_result = detection_result
            elif prev_result is not None:
                # Reusar detecciones anteriores para overlay (sin recalcular)
                slot_detections = prev_result.detections

            if overlay is not None:
                drawn = overlay.draw_overlay(frame, slot_detections)
                frame_b64 = overlay.encode_frame(drawn)
            else:
                frame_b64 = None

            should_stop = callback(frame_b64, detection_result, events)
            if should_stop:
                break


# ====================================================================== #
#  Test manual — Fase INT-1 (Cámara → Detección → Overlay integrados)
# ====================================================================== #
if __name__ == "__main__":
    from detection_engine import DetectionEngine
    from video_overlay import VideoOverlay

    # --- Inicializar componentes ---
    print("=== INT-1: Cámara → Detección ===\n")

    print("[1/3] Cargando DetectionEngine...")
    engine = DetectionEngine()

    print("[2/3] Creando VideoOverlay...")
    overlay = VideoOverlay()

    print("[3/3] Iniciando CameraCapture...")
    cam = CameraCapture()  # RTSP por defecto, fallback a USB
    if not cam.start():
        raise SystemExit(1)

    state = {"count": 0, "events_total": 0}
    t_start = time.time()

    def on_frame(frame_b64, detection_result, events):
        state["count"] += 1

        if events:
            for ev in events:
                state["events_total"] += 1
                ts = ev.timestamp.strftime('%H:%M:%S')
                print(f"  ⚡ [{ts}] {ev.event_type.value.upper()}: {ev.sku_name} "
                      f"({ev.count_before}→{ev.count_after}) conf={ev.confidence:.2f}")

        return False  # nunca detenerse — modo en vivo continuo

    try:
        cam.stream_loop(
            detection_engine=engine,
            overlay=overlay,
            callback=on_frame,
            max_fps=5,
        )
    finally:
        elapsed = time.time() - t_start
        actual_fps = state["count"] / elapsed if elapsed > 0 else 0
        print(f"\n{'='*50}")
        print(f"{state['count']} frames en {elapsed:.1f}s — {actual_fps:.1f} FPS")
        print(f"Eventos detectados: {state['events_total']}")
        print(f"{'='*50}")
        cam.stop()
