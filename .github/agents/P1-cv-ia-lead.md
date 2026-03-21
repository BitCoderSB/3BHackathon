# Contexto para Copilot — P1: CV/IA Lead (Módulo M2)

## Tu rol
Eres el responsable de **entrenar el modelo YOLOv8-seg** y construir el **pipeline de detección en tiempo real**. Tu módulo es el corazón del sistema: si tu modelo no detecta bien, nada funciona.

## Tu módulo: M2 — Motor de Visión por Computadora

### Archivos que te importan
- `assets/project-7-at-2026-03-20-21-09-0e2e8304/` → Dataset completo (images + labels)
- `assets/project-7-at-2026-03-20-21-09-0e2e8304/classes.txt` → 7 clases
- `backend/cv_engine.py` → Tu archivo principal
- `models/best.pt` → Donde guardarás el modelo entrenado

### Dataset
- **71 imágenes** JPG del anaquel, tomadas desde 2 cámaras
- **Labels en formato YOLO POLYGON** (segmentación, NO bbox) — cada línea es `class_id x1 y1 x2 y2 ...`
- 7 clases: agua_burst(0), burst_energetica_roja(1), burst_energy(2), nachos_naturasol(3), nebraska_mango(4), sisi_cola(5), sun_paradise_naranja(6)

### Cómo entrenar
```python
from ultralytics import YOLO

# Crear dataset.yaml apuntando a las carpetas de images/ y labels/
# IMPORTANTE: task=segment porque los labels son polígonos

model = YOLO("yolov8n-seg.pt")  # nano para velocidad, o yolov8s-seg para precisión
results = model.train(
    data="dataset.yaml",
    epochs=100,
    imgsz=640,
    task="segment",
    batch=8,
    name="anaquel_3b"
)
```

### Tu output (contratos)
Debes producir 3 tipos de datos que otros módulos consumen:

**1. DetectionEvent → para M3 (Inventario)**
```python
@dataclass
class DetectionEvent:
    event_id: str              # UUID
    event_type: EventType      # RETIRO o DEVOLUCION
    sku_id: str                # ej: "agua_burst"
    sku_name: str              # ej: "Agua Natural Burst 1500ml"
    slot_id: int               # 1-7
    confidence: float          # 0.0-1.0
    timestamp: datetime
    bbox: tuple[int,int,int,int]
    count_before: int
    count_after: int
```

**2. AnnotatedFrame → para M5 (Video Overlay)**
```python
@dataclass
class AnnotatedFrame:
    frame: np.ndarray
    timestamp: float
    detections: list[SlotDetection]
```

**3. InteractionEvent → para M7 (Heatmap)**
```python
@dataclass
class InteractionEvent:
    slot_id: int
    sku_id: str
    region: tuple[int,int,int,int]
    timestamp: datetime
    interaction_type: str  # "hand_detected" | "product_moved"
```

### Lógica anti-falsos positivos
- **Cooldown por slot:** No emitir 2 eventos del mismo slot en < 3 segundos
- **Doble validación:** Solo emitir si el cambio de conteo persiste en ≥3 frames consecutivos
- **Umbral de confianza:** ≥ 0.70 (configurable)
- **Warm-up:** Ejecutar 3 inferences dummy al iniciar

### Prioridades
1. 🔴 Modelo que detecte los 7 SKUs con mAP ≥ 0.80
2. 🔴 Conteo por slot funcional
3. 🔴 Generación de DetectionEvent al detectar cambio
4. 🟡 Doble validación + cooldown
5. 🟡 AnnotatedFrame para overlay
6. 🟢 InteractionEvent para heatmap

### Si terminas antes
Ayuda con: data augmentation, ajustar confianza/cooldown, integración con M3, testing end-to-end.
