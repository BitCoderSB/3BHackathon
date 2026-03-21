# Contexto para Copilot — P2: CV/Cámara (Módulos M1 + M5)

## Tu rol
Eres el responsable de la **captura de video** (conexión con cámaras RTSP y USB) y del **overlay visual** (dibujar bounding boxes, etiquetas y semáforos sobre el video). Tu trabajo conecta la cámara física con el modelo de CV, y genera el video enriquecido que se muestra en el dashboard.

## Tus módulos

### M1 — Captura de Video
**Archivo:** `backend/camera_capture.py`

#### Cámaras RTSP del hackathon
```python
RTSP_CAMARAS = [
    "rtsp://admin:admin1234@172.31.13.190:554/cam/realmonitor?channel=1&subtype=0",
    "rtsp://admin:admin1234@172.31.13.191:554/cam/realmonitor?channel=1&subtype=0"
]
# Credenciales: admin / admin1234
# Fallback: cámara USB local (índice 0)
```

#### Output que produces (Contrato C1)
```python
@dataclass
class FrameData:
    frame: np.ndarray        # BGR, shape (H, W, 3), uint8
    timestamp: float          # time.time()
    frame_id: int             # Secuencial
    resolution: tuple[int, int]  # (width, height)

def get_frames() -> Generator[FrameData, None, None]:
    """Generador que yield frames desde la cámara."""
```

#### Requisitos clave
- Stream estable a ≥10 FPS
- Soportar RTSP, USB (índice 0) y video pregrabado (.mp4)
- Reconexión automática si la cámara se desconecta (reintentar cada 2s, máx 10)
- Resolución configurable (default 1280x720)

### M5 — Video Overlay Aumentado
**Archivo:** `backend/video_overlay.py`

#### Input que recibes de M2
```python
@dataclass
class AnnotatedFrame:
    frame: np.ndarray
    timestamp: float
    detections: list[SlotDetection]

@dataclass
class SlotDetection:
    sku_id: str
    sku_name: str
    slot_id: int
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    count: int
    stock_level: str  # "ok" | "warning" | "critical"
```

#### Lo que debes dibujar
- **Bounding boxes** con color según stock_level: verde (ok), amarillo (warning), rojo (critical)
- **Etiqueta** con nombre de SKU + conteo actual
- **Flash/parpadeo** breve al detectar retiro o devolución
- Codificar como **JPEG base64** para transmitir vía WebSocket (calidad 80%)
- Mantener **≥5 FPS** en el stream

### Mock para desarrollo sin M2
```python
# Genera detecciones fake sobre un video cualquiera
fake_detections = [
    SlotDetection(sku_id="agua_burst", sku_name="Agua Natural Burst", slot_id=1,
                  bbox=(100, 200, 300, 400), confidence=0.95, count=6, stock_level="ok"),
    SlotDetection(sku_id="sisi_cola", sku_name="Sisi Cola", slot_id=6,
                  bbox=(500, 200, 700, 400), confidence=0.88, count=2, stock_level="critical"),
]
```

### Prioridades
1. 🔴 Captura de video estable (RTSP → USB fallback → video archivo)
2. 🔴 Generador de FrameData funcional
3. 🟡 Overlay con bounding boxes + etiquetas
4. 🟡 Colores semáforo
5. 🟡 Codificación JPEG/base64 para stream
6. 🟢 Animación de flash al retiro

### Si terminas antes
Ayuda con: integración M1↔M2, testing con cámara real, mejorar rendimiento del stream, integración con dashboard para mostrar video.
