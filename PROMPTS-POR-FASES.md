# Prompts por Fases — Hackathon Tiendas 3B

Cada persona debe enviar los prompts **en orden**, verificando el test manual de cada fase **antes** de pasar a la siguiente. NO avanzar si el test falla.

---

## 👤 P1 — CV/IA Lead (M2: Motor de Detección)

### Fase 1.1 — Preparar dataset YOLO
```
@P1-cv-ia-lead Lee tu contexto en .github/agents/P1-cv-ia-lead.md.

Crea el archivo backend/dataset.yaml para entrenar YOLOv8-seg con el dataset 
que está en assets/project-7-at-2026-03-20-21-09-0e2e8304/. 

Las 7 clases están en assets/project-7-at-2026-03-20-21-09-0e2e8304/classes.txt.
Las imágenes en images/ y los labels YOLO polygon en labels/.

El yaml debe apuntar con rutas absolutas o relativas correctas. 
NO muevas ni copies las imágenes, referencia la carpeta existente.
Separa 80/20 train/val si es necesario.
```

**✅ Test manual Fase 1.1:**
```powershell
# Verificar que el archivo existe y tiene rutas correctas
cat backend/dataset.yaml
# Verificar que las rutas a imágenes/labels existen
Test-Path (Get-Content backend/dataset.yaml | Select-String "train:" | ForEach-Object { $_.Line.Split(": ")[1].Trim() })
```

---

### Fase 1.2 — Entrenar modelo YOLOv8-seg
```
@P1-cv-ia-lead Crea el script backend/train_model.py que:

1. Cargue el modelo base yolov8n-seg.pt (nano para velocidad en hackathon)
2. Entrene con backend/dataset.yaml, task="segment"
3. Parámetros: epochs=50, imgsz=640, batch=8, device="cpu" (o "0" si hay GPU)
4. Guarde el mejor modelo en models/best.pt
5. Imprima métricas de entrenamiento al final (mAP, precision, recall)

Solo el script de entrenamiento, nada más.
```

**✅ Test manual Fase 1.2:**
```powershell
# Activar venv y ejecutar entrenamiento
.\backend\.venv\Scripts\Activate.ps1
python backend/train_model.py
# VERIFICAR: Debe completar el entrenamiento sin errores
# VERIFICAR: Debe existir models/best.pt (o runs/segment/train/weights/best.pt)
Test-Path models/best.pt
```

---

### Fase 1.3 — Motor de detección con inferencia
```
@P1-cv-ia-lead Crea backend/detection_engine.py con la clase DetectionEngine que:

1. En __init__ cargue el modelo desde models/best.pt
2. Tenga método detect(frame: np.ndarray) -> DetectionResult que:
   - Ejecute model.predict(frame, task="segment", conf=0.5)
   - Cuente cuántas instancias hay de cada clase
   - Retorne un DetectionResult con la lista de detecciones
3. Tenga método compare(prev: DetectionResult, curr: DetectionResult) -> list[DetectionEvent] que:
   - Compare conteos entre dos frames consecutivos
   - Si count baja → genere DetectionEvent tipo RETIRO
   - Si count sube → genere DetectionEvent tipo DEVOLUCION
   - Solo genere evento si la diferencia es consistente por 3 frames (anti-flicker)

Usa los dataclasses de los contratos C2 y C3 definidos en mvp-requisitos-y-dependencias.md.
Incluye un if __name__ == "__main__" que pruebe con una imagen de assets/.
```

**✅ Test manual Fase 1.3:**
```powershell
python backend/detection_engine.py
# VERIFICAR: Debe cargar el modelo sin error
# VERIFICAR: Debe procesar una imagen y mostrar detecciones con conteos
# VERIFICAR: Debe imprimir algo como: "agua_burst: 3, nachos_naturasol: 2, ..."
```

---

## 👤 P2 — CV/Cámara (M1 + M5)

### Fase 2.1 — Captura de cámara básica
```
@P2-cv-camera Lee tu contexto en .github/agents/P2-cv-camera.md.

Crea backend/camera_capture.py con la clase CameraCapture que:

1. Acepte una fuente en __init__(source): str RTSP URL o int para USB
2. Tenga método start() que abra cv2.VideoCapture(source)
3. Tenga generador get_frames() que yield FrameData (frame numpy, timestamp, frame_id, resolution)
4. Tenga método stop() que libere la cámara
5. Manejo de reconexión: si se pierde la conexión RTSP, reintentar cada 3 segundos (max 5 intentos)
6. Fallback: si RTSP falla después de 5 intentos, intentar cámara USB índice 0

Incluye un if __name__ == "__main__" que abra la cámara, capture 10 frames, 
imprima la resolución de cada uno y cierre.
NO abras ventana de OpenCV (sin cv2.imshow), solo imprime datos en consola.
```

**✅ Test manual Fase 2.1:**
```powershell
python backend/camera_capture.py
# VERIFICAR: Debe conectar a cámara (RTSP o USB fallback)
# VERIFICAR: Debe imprimir 10 líneas tipo: "Frame 1: 2592x1944 @ 1711036321.5"
# VERIFICAR: Debe cerrar sin error
```

---

### Fase 2.2 — Video overlay con bounding boxes
```
@P2-cv-camera Crea backend/video_overlay.py con la clase VideoOverlay que:

1. Tenga método draw_overlay(frame, detections) -> np.ndarray que:
   - Dibuje bounding box por cada detección
   - Color semáforo: verde si stock >50%, amarillo 25-50%, rojo <25%
   - Texto encima del box: "{sku_name} x{count}" con fondo semitransparente
   - Dibuje un pequeño semáforo (círculo) en esquina superior derecha del box
2. Tenga método encode_frame(frame) -> str que:
   - Convierta el frame a JPEG (quality=70 para velocidad)
   - Lo codifique a base64
   - Retorne el string base64
3. Tenga método draw_status_bar(frame, inventory_summary) -> np.ndarray que:
   - Dibuje una barra en la parte inferior del frame
   - Muestre resumen: "Stock total: X/56 | Alertas: N"

Incluye un if __name__ == "__main__" que:
- Cargue UNA imagen de assets/project-7-.../images/
- Dibuje 3 bounding boxes ficticios con distintos niveles de stock
- Guarde el resultado como test_overlay.jpg
```

**✅ Test manual Fase 2.2:**
```powershell
python backend/video_overlay.py
# VERIFICAR: Debe crear test_overlay.jpg
# VERIFICAR: Abrir la imagen y ver 3 bounding boxes con colores distintos
# VERIFICAR: Debe verse texto legible encima de cada box
```

---

### Fase 2.3 — Encoding base64 y streaming loop
```
@P2-cv-camera Agrega al archivo backend/camera_capture.py un método 
stream_loop(detection_engine, overlay, callback) que:

1. Capture frames continuamente con get_frames()
2. Llame a detection_engine.detect(frame) para obtener detecciones  
3. Llame a overlay.draw_overlay(frame, detections) para dibujar
4. Llame a overlay.encode_frame(frame) para obtener base64
5. Llame a callback(frame_base64, detections) para enviar al API
6. Controle el FPS: máximo 5 frames/segundo procesados (skip frames si la cámara da más)
7. Si detection_engine es None, solo haga captura + encode (modo sin CV)

Incluye un if __name__ == "__main__" que ejecute stream_loop sin detection_engine 
(None), imprima el tamaño en KB de cada frame base64, y se detenga a los 20 frames.
```

**✅ Test manual Fase 2.3:**
```powershell
python backend/camera_capture.py
# VERIFICAR: Debe imprimir 20 líneas tipo: "Frame 1: 45.2 KB base64"
# VERIFICAR: No debe procesar más de 5 frames por segundo
# VERIFICAR: Debe detenerse solo después de 20 frames
```

---

## 👤 P3 — Backend Core (M3 + M4)

### Fase 3.1 — Motor de inventario
```
@P3-backend-core Lee tu contexto en .github/agents/P3-backend-core.md.

Crea backend/inventory_engine.py con la clase InventoryEngine que:

1. En __init__ inicialice los 7 productos reales con stock_initial=8 cada uno:
   agua_burst, burst_energetica_roja, burst_energy, nachos_naturasol,
   nebraska_mango, sisi_cola, sun_paradise_naranja
   (nombres completos en .github/copilot-instructions.md)
2. Tenga método process_event(event: DetectionEvent) -> InventoryEvent que:
   - Actualice stock_current del SKU correspondiente
   - Valide que stock no baje de 0 ni suba de stock_initial
   - Genere alertas si stock <= 25% del inicial (threshold configurable)
   - Retorne un InventoryEvent con before/after
3. Tenga método get_state() -> InventoryState (estado completo)
4. Tenga método get_history(sku_id) -> SKUHistory (para predicciones)
5. Tenga método reset() que reinicie todo a stock_initial
6. Registre callbacks: on_event, on_alert para notificar a otros módulos

Incluye un if __name__ == "__main__" que:
- Cree el engine
- Simule 5 retiros del producto "nachos_naturasol" uno por uno
- Imprima el estado después de cada retiro
- Verifique que se genera alerta cuando stock llega a 2 (25% de 8)
```

**✅ Test manual Fase 3.1:**
```powershell
python backend/inventory_engine.py
# VERIFICAR: Stock de nachos baja: 8→7→6→5→4→3
# VERIFICAR: En stock=2, debe imprimir "ALERTA: nachos_naturasol stock bajo"
# VERIFICAR: get_state() muestra los 7 productos, 6 en stock=8 y nachos en stock=3
```

---

### Fase 3.2 — API REST con FastAPI
```
@P3-backend-core Crea backend/main.py con la API FastAPI que:

1. Importe e instancie InventoryEngine
2. Implemente estos endpoints REST:
   - GET /api/inventory → InventoryState completo
   - GET /api/inventory/{sku_id} → ProductStock de un SKU
   - GET /api/events?limit=50 → últimos N InventoryEvents
   - GET /api/predictions → list (vacía por ahora, P4 lo conectará)
   - GET /api/heatmap → dict (vacío por ahora)
   - GET /api/narratives → list (vacía por ahora)
   - POST /api/inventory/reset → reinicia inventario
   - GET /api/health → { status: "ok", uptime: float }
3. Incluye CORS middleware (allow all origins para desarrollo)
4. NO incluyas WebSocket todavía, eso es Fase 3.3

Incluye al final:
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**✅ Test manual Fase 3.2:**
```powershell
cd backend; python main.py
# En otra terminal:
Invoke-RestMethod http://localhost:8000/api/health
# VERIFICAR: { status: "ok", uptime: X.X }

Invoke-RestMethod http://localhost:8000/api/inventory
# VERIFICAR: Muestra 7 productos, todos con stock_current=8

Invoke-RestMethod -Method Post http://localhost:8000/api/inventory/reset
# VERIFICAR: Responde con éxito

# Abrir navegador en http://localhost:8000/docs
# VERIFICAR: Swagger UI muestra todos los endpoints
```

---

### Fase 3.3 — WebSocket con python-socketio
```
@P3-backend-core Agrega WebSocket a backend/main.py usando python-socketio:

1. Crea un servidor socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
2. Monta la app ASGI combinando FastAPI + socketio
3. Evento "connect": log de conexión
4. Evento "disconnect": log de desconexión
5. Crea función broadcast_event(event_type, data) que emita a todos los clientes
6. Conecta los callbacks de InventoryEngine:
   - on_event → emite "inventory_update" + "detection_event" por WebSocket
   - on_alert → emite "alert" por WebSocket
7. Agrega endpoint POST /api/mock/event que simule un retiro aleatorio 
   (para probar WebSocket sin CV). Debe llamar a process_event y provocar 
   el broadcast por WebSocket.

NO toques los endpoints REST de la Fase 3.2, solo agrega WebSocket.
```

**✅ Test manual Fase 3.3:**
```powershell
cd backend; python main.py
# En otra terminal, probar con Python:
python -c "
import socketio
sio = socketio.Client()

@sio.on('inventory_update')
def on_update(data):
    print('UPDATE:', data)

@sio.on('alert')
def on_alert(data):
    print('ALERT:', data)

sio.connect('http://localhost:8000')
print('Conectado! Esperando eventos...')
sio.wait()
"
# En otra terminal, disparar evento mock:
Invoke-RestMethod -Method Post http://localhost:8000/api/mock/event
# VERIFICAR: El cliente Python recibe el evento "inventory_update"
# Repetir hasta que haya alerta (stock bajo)
# VERIFICAR: El cliente recibe "alert" cuando stock <= 25%
```

---

## 👤 P4 — Backend Inteligencia (M6 + M7 + M8)

### Fase 4.1 — Motor de predicción
```
@P4-backend-intelligence Lee tu contexto en .github/agents/P4-backend-intelligence.md.

Crea backend/prediction_engine.py con la clase PredictionEngine que:

1. Tenga método predict(history: SKUHistory) -> StockPrediction que:
   - Calcule intervalos entre retiros (timestamps) en minutos
   - Aplique suavizado exponencial (alpha=0.3) sobre los intervalos
   - Calcule rate_per_hour y minutes_remaining
   - Determine trend: comparar primera mitad vs segunda mitad de intervalos
   - Determine confidence: alta (>6 eventos), media (>3), baja (<=3)
   - Si hay menos de 2 eventos, retorne minutes_remaining=None, confidence="baja"
2. Tenga método predict_all(histories: list[SKUHistory]) -> list[StockPrediction]

Incluye un if __name__ == "__main__" que:
- Cree un SKUHistory fake para "nachos_naturasol" con 6 retiros separados por 
  5 min, 4 min, 3 min, 3 min, 2 min (acelerando)
- Stock actual: 2, stock inicial: 8
- Imprima la predicción completa
- Verifique que trend sea "acelerando"
```

**✅ Test manual Fase 4.1:**
```powershell
python backend/prediction_engine.py
# VERIFICAR: Imprime predicción con rate_per_hour > 0
# VERIFICAR: minutes_remaining es un número razonable (no negativo, no infinito)
# VERIFICAR: trend = "acelerando" (los intervalos se acortan)
# VERIFICAR: confidence = "alta" (6 eventos)
```

---

### Fase 4.2 — Motor de narración
```
@P4-backend-intelligence Crea backend/narrative_engine.py con la clase NarrativeEngine que:

1. Tenga diccionario TEMPLATES con mensajes en español para:
   retiro, devolucion, alerta_umbral, prediccion, todo_ok, resumen, alta_demanda
2. Tenga método generate(event_type: str, **kwargs) -> NarrativeMessage que:
   - Seleccione el template correcto
   - Formatee con los kwargs (sku_name, stock, minutes, etc.)
   - Asigne severity: info (retiro/devolucion), warning (prediccion), critical (alerta)
   - Asigne icon emoji según tipo
3. Tenga _cooldown: dict que evite repetir mismo tipo+sku en menos de 30 segundos
4. Tenga método get_recent(limit=50) -> list[NarrativeMessage] (últimas N narrativas)

Incluye un if __name__ == "__main__" que:
- Genere una narrativa de retiro para "nachos_naturasol" stock=4
- Genere una narrativa de alerta para "nachos_naturasol" stock=2, pct=25
- Genere una narrativa de predicción para "nachos_naturasol" minutes=15
- Intente generar otra alerta para nachos antes de 30s (debe ser bloqueada por cooldown)
- Imprima todas las narrativas generadas
```

**✅ Test manual Fase 4.2:**
```powershell
python backend/narrative_engine.py
# VERIFICAR: Imprime 3 narrativas en español con emoji
# VERIFICAR: La 4ta narrativa (repetida) dice "bloqueada por cooldown" o similar
# VERIFICAR: Severidades correctas: info, critical, warning
```

---

### Fase 4.3 — Motor de heatmap
```
@P4-backend-intelligence Crea backend/heatmap_engine.py con la clase HeatmapEngine que:

1. Tenga método record(interaction: InteractionEvent) que acumule por slot_id
2. Tenga método get_heatmap(window_seconds=300) -> dict que:
   - Filtre interacciones dentro de la ventana temporal
   - Cuente por slot_id
   - Normalice intensidad (slot más activo = 1.0, resto proporcional)
   - Retorne formato: { "slots": [...], "window_seconds": N, "last_updated": ISO }
3. Tenga método reset() que limpie todo

Incluye un if __name__ == "__main__" que:
- Registre 10 interacciones: 5 en slot 3, 3 en slot 1, 2 en slot 5
- Imprima el heatmap
- Verifique que slot 3 tiene intensity=1.0, slot 1 ≈0.6, slot 5 ≈0.4
```

**✅ Test manual Fase 4.3:**
```powershell
python backend/heatmap_engine.py
# VERIFICAR: slot 3 intensity = 1.0
# VERIFICAR: slot 1 intensity ≈ 0.6
# VERIFICAR: slot 5 intensity ≈ 0.4
# VERIFICAR: last_updated es un timestamp ISO válido
```

---

## 👤 P5 — Frontend Dashboard (M9)

### Fase 5.1 — Scaffold React + Layout base
```
@P5-frontend Lee tu contexto en .github/agents/P5-frontend.md.

Ejecuta en terminal: cd frontend; npm install

Luego crea la estructura base:
- src/main.tsx — entry point que renderiza <App />
- src/App.tsx — layout grid con 6 zonas placeholder:
  VideoFeed (izquierda), StockPanel (derecha arriba), PredictionCards (derecha medio),
  HeatmapGrid (izquierda abajo), NarrativeLog (derecha abajo), EventTimeline (abajo)
- src/index.css — ya tiene @tailwind directives, no lo modifiques
- Cada zona debe ser un <div> con borde punteado, nombre del componente como texto 
  centrado, y tamaño mínimo visible
- Header: "🏪 Inventario en Tiempo Real — Tiendas 3B" con bg-blue-800

NO crees los componentes reales todavía, solo el layout con placeholders.
Usa CSS Grid o Tailwind grid para el layout responsive.
```

**✅ Test manual Fase 5.1:**
```powershell
cd frontend; npm run dev
# Abrir http://localhost:3000
# VERIFICAR: Se ve el header azul con el título
# VERIFICAR: Se ven 6 zonas con borde punteado y texto placeholder
# VERIFICAR: El layout se ve ordenado y con grid correcto
```

---

### Fase 5.2 — StockPanel con datos mock
```
@P5-frontend Crea el componente src/components/StockPanel.tsx que:

1. Reciba props: products: ProductStock[] (usa el type de tu contexto P5)
2. Muestre una card por producto con:
   - Nombre del producto
   - Barra horizontal de progreso: stock_current / stock_initial
   - Color semáforo: verde (>50%), amarillo (25-50%), rojo (<25%)
   - Texto: "X / 8 unidades"
   - Badge "ALERTA" si alert_active es true
3. Animación/transición CSS cuando cambia el valor de stock

Crea también src/mocks/mockData.ts con los 7 productos con datos iniciales.
Integra StockPanel en App.tsx reemplazando el placeholder, usando los datos mock.
```

**✅ Test manual Fase 5.2:**
```powershell
# Con el dev server corriendo:
# Abrir http://localhost:3000
# VERIFICAR: Se ven 7 cards de productos con barras de progreso
# VERIFICAR: Todas las barras en verde (8/8 = 100%)
# VERIFICAR: Nombres correctos de los 7 productos reales
```

---

### Fase 5.3 — NarrativeLog + mock events con timer
```
@P5-frontend Crea:

1. src/components/NarrativeLog.tsx que:
   - Reciba messages: NarrativeMessage[] como prop
   - Muestre cada mensaje con: icon + timestamp (HH:MM:SS) + texto
   - Color de fondo según severity: gris info, amarillo warning, rojo critical
   - Auto-scroll hacia el último mensaje
   - Max visible: últimos 20 mensajes con scroll

2. Crea un hook src/hooks/useMockSimulation.ts que:
   - Simule retiros aleatorios cada 4 segundos
   - Actualice el array de products (decrementar stock)
   - Genere NarrativeMessage correspondientes
   - Cuando un stock baje de 25%, genere mensaje critical

Integra NarrativeLog en App.tsx. El StockPanel debe actualizarse automáticamente
con la simulación (las barras deben bajar y cambiar de color).
```

**✅ Test manual Fase 5.3:**
```powershell
# Abrir http://localhost:3000
# VERIFICAR: Cada ~4 seg aparece un nuevo mensaje en el log
# VERIFICAR: Las barras de stock bajan progresivamente
# VERIFICAR: Cuando un producto baja de 25%, la barra se pone roja
# VERIFICAR: Aparece un mensaje rojo critical en el log
# VERIFICAR: El log hace auto-scroll
```

---

### Fase 5.4 — VideoFeed + conexión WebSocket real
```
@P5-frontend Crea:

1. src/components/VideoFeed.tsx que:
   - Muestre una imagen <img> que se actualiza con cada frame
   - Reciba frame como string base64
   - Muestre indicador "🔴 EN VIVO" o "⚫ SIN SEÑAL" según si hay frames
   - Si no hay frames en 5 segundos, mostrar "SIN SEÑAL"

2. src/hooks/useSocket.ts que:
   - Conecte a socket.io en http://localhost:8000
   - Escuche eventos: inventory_update, detection_event, video_frame, 
     prediction_update, heatmap_update, narrative, alert
   - Exponga estado reactivo para cada tipo de dato
   - Tenga fallback: si no puede conectar en 3 segundos, usar datos mock
   
Integra useSocket en App.tsx. Si hay backend, usa datos reales.
Si no hay backend, cae automáticamente a la simulación mock de Fase 5.3.
```

**✅ Test manual Fase 5.4:**
```powershell
# SIN backend corriendo:
# Abrir http://localhost:3000
# VERIFICAR: VideoFeed muestra "SIN SEÑAL"
# VERIFICAR: El resto del dashboard funciona con datos mock

# CON backend corriendo (si P3 terminó Fase 3.3):
cd backend; python main.py
# Abrir http://localhost:3000
# VERIFICAR: Conecta por WebSocket (ver consola del navegador)
# Disparar: Invoke-RestMethod -Method Post http://localhost:8000/api/mock/event
# VERIFICAR: El stock se actualiza en el dashboard en tiempo real
```

---

### Fase 5.5 — PredictionCards + HeatmapGrid + EventTimeline
```
@P5-frontend Crea los 3 componentes restantes:

1. src/components/PredictionCards.tsx:
   - Card por SKU con: rate_per_hour, minutes_remaining, trend (↑↓→)
   - Badge de confidence (alta=verde, media=amarillo, baja=gris)
   - Resaltar productos que se agotan en < 30 min

2. src/components/HeatmapGrid.tsx:
   - Grid visual representando el anaquel (7 slots)
   - Color por intensidad: azul frío (0.0) → rojo caliente (1.0)
   - Tooltip al hover: "slot_id: X, actividad: N"

3. src/components/EventTimeline.tsx:
   - Usar Recharts LineChart
   - Línea de stock por SKU a lo largo del tiempo
   - Eje X: tiempo (minutos), Eje Y: unidades (0-8)
   - Una línea por producto con colores distintos

Integra los 3 en App.tsx reemplazando los placeholders restantes.
Alimenta con datos del mock o WebSocket según disponibilidad.
```

**✅ Test manual Fase 5.5:**
```powershell
# Abrir http://localhost:3000
# VERIFICAR: PredictionCards muestra cards con tiempos y tendencias
# VERIFICAR: HeatmapGrid muestra 7 slots con colores
# VERIFICAR: EventTimeline muestra gráfica Recharts con líneas por producto
# VERIFICAR: Todo se actualiza con la simulación mock
# VERIFICAR: Dashboard completo, sin placeholders restantes
```

---

## 🔗 Fases de Integración (Todo el equipo)

### Fase INT-1 — P2 + P1: Cámara → Detección
```
Integrar camera_capture con detection_engine:
- P2 ejecuta stream_loop pasando el DetectionEngine de P1
- Verificar que detecta productos en los frames de la cámara real
```
**✅ Test:** Ejecutar stream y ver en consola detecciones con conteos correctos.

### Fase INT-2 — P1 + P3: Detección → Inventario
```
Conectar DetectionEvents del detector al InventoryEngine:
- Cada detección de retiro/devolución actualiza el inventario
- El inventario emite por WebSocket
```
**✅ Test:** Retirar un producto del anaquel → el endpoint `/api/inventory` refleja el cambio.

### Fase INT-3 — P3 + P4: Inventario → Inteligencia
```
Conectar InventoryEngine con PredictionEngine, NarrativeEngine, HeatmapEngine:
- Cada evento del inventario alimenta los 3 motores
- Las predicciones y narrativas se emiten por WebSocket
```
**✅ Test:** Hacer 4 retiros → la predicción muestra minutos restantes, la narrativa genera mensajes.

### Fase INT-4 — Todo → P5: Dashboard completo
```
Verificar que el dashboard recibe y muestra TODO en tiempo real:
- Video con overlay, stock, predicciones, narrativa, heatmap, timeline
```
**✅ Test:** Retirar un producto del anaquel físico → todo el dashboard se actualiza en < 2 segundos.
