# Flujo de Trabajo — Hackathon Tiendas 3B

## 🚀 Setup Inicial (Todos)

```powershell
# 1. Clonar/descargar el proyecto
# 2. Desde la raíz del proyecto:
.\scripts\setup-all.ps1
```

Esto instala **todas las dependencias** de backend (Python) y frontend (Node/React).

---

## 👥 Asignación de Personas

| Persona | Rol | Módulos | Archivos principales |
|---------|-----|---------|---------------------|
| **P1** | CV/IA Lead | M2 | `backend/detection_engine.py` |
| **P2** | CV/Cámara | M1, M5 | `backend/camera_capture.py`, `backend/video_overlay.py` |
| **P3** | Backend Core | M3, M4 | `backend/inventory_engine.py`, `backend/main.py` |
| **P4** | Backend Intel | M6, M7, M8 | `backend/prediction_engine.py`, `backend/heatmap_engine.py`, `backend/narrative_engine.py` |
| **P5** | Frontend | M9 | `frontend/src/**` |

Cada persona tiene su archivo de contexto en `.github/agents/P{N}-*.md` — **léelo antes de empezar**.

---

## 📁 Regla de Archivos

Cada persona trabaja **solo en sus archivos asignados**. No tocar archivos de otros sin avisar.

```
backend/
├── main.py                 ← P3 (API + WebSocket)
├── config.py               ← P3 (configuración compartida)
├── camera_capture.py       ← P2 (captura de cámara)
├── detection_engine.py     ← P1 (motor CV)
├── inventory_engine.py     ← P3 (motor inventario)
├── video_overlay.py        ← P2 (overlay visual)
├── prediction_engine.py    ← P4 (predicciones)
├── heatmap_engine.py       ← P4 (heatmap)
├── narrative_engine.py     ← P4 (narración)
└── requirements.txt        ← Compartido

frontend/
└── src/                    ← P5 (todo el frontend)
```

---

## 🔄 Flujo de Integración

### Fase 1 — Desarrollo Independiente (Primeras 2-3 horas)
Cada persona trabaja con **mocks** sin depender de los demás.

- **P1**: Entrena/prueba YOLOv8-seg con el dataset, exporta `detect(frame) → DetectionResult`
- **P2**: Captura frames de cámara RTSP, prueba con video local
- **P3**: Crea API REST + WebSocket, InventoryEngine con mock events
- **P4**: PredictionEngine + NarrativeEngine con datos fake
- **P5**: Dashboard completo con mock data (sin backend)

### Fase 2 — Integración por Pares (Hora 3-4)
```
P2 (cámara) ──→ P1 (CV) ──→ P3 (inventario + API)
                                      │
                              P4 (predicción/narrativa)
                                      │
                              P5 (dashboard vía WebSocket)
```

Orden de integración:
1. **P2 + P1**: Cámara envía frames → detector procesa → `DetectionResult`
2. **P1 + P3**: Detector envía `DetectionEvent` → inventario actualiza
3. **P3 + P4**: Inventario envía historial → predicción + narrativa
4. **P3 + P5**: API/WebSocket envía todo → dashboard muestra

### Fase 3 — Pulir + Demo (Última hora)
- Bug fixes de integración
- Ajustar umbrales de detección
- Pulir UI para el pitch
- Ensayar demo en vivo

---

## 📡 Comunicación

### Contratos entre módulos
Los **contratos** están definidos en `mvp-requisitos-y-dependencias.md`. Son las interfaces (dataclasses/types) que conectan módulos. **No cambiar un contrato sin avisar al equipo.**

### Si necesitas algo de otro módulo
1. Primero usa el **mock** definido en tu archivo de contexto
2. Cuando la persona termine su módulo, integra el real
3. Si necesitas cambiar un contrato, avisa en el grupo

### Canales rápidos
- **Bloqueante**: Grita en persona / mensaje directo
- **No bloqueante**: Comenta en el grupo del hackathon
- **Merge conflict**: Coordinar quién toca qué archivo (ver regla arriba)

---

## 🧪 Cómo probar

### Backend
```powershell
# Activar entorno virtual
.\backend\.venv\Scripts\Activate.ps1

# Iniciar servidor
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Docs interactivos
# http://localhost:8000/docs
```

### Frontend
```powershell
cd frontend
npm run dev

# Dashboard
# http://localhost:3000
```

### CV / Modelo
```python
from ultralytics import YOLO

# Entrenar (P1)
model = YOLO("yolov8n-seg.pt")
model.train(data="dataset.yaml", task="segment", epochs=50, imgsz=640)

# Inferencia (P1/P2)
model = YOLO("models/best.pt")
results = model.predict(source=frame, task="segment", conf=0.5)
```

---

## ⏰ Timeline Sugerido

| Hora | Actividad | Quién |
|------|-----------|-------|
| 0:00 | Setup + leer contexto | Todos |
| 0:30 | Desarrollo independiente con mocks | Todos |
| 2:30 | P2+P1 integración cámara→CV | P1, P2 |
| 3:00 | P1+P3 integración CV→inventario | P1, P3 |
| 3:15 | P3+P4 integración inventario→inteligencia | P3, P4 |
| 3:30 | P3+P5 integración API→dashboard | P3, P5 |
| 4:00 | Integración completa end-to-end | Todos |
| 4:30 | Bug fixes + pulir demo | Todos |
| 5:00 | Ensayo del pitch | Todos |
| 5:30 | **DEMO** 🎬 | Todos |

---

## 🎯 Checklist Pre-Demo

- [ ] Cámara RTSP conectada y mostrando video
- [ ] YOLOv8-seg detectando los 7 productos
- [ ] Dashboard mostrando stock en tiempo real
- [ ] Retirar un producto → stock se actualiza automáticamente
- [ ] Alertas aparecen cuando stock < 25%
- [ ] Predicción muestra "se agota en X min"
- [ ] Heatmap muestra zonas calientes
- [ ] Narrativa genera mensajes automáticos
- [ ] Video con overlay (bounding boxes + semáforo)

---

## 💡 Tips para el Pitch

1. **Demo en vivo primero** — Impacto visual inmediato
2. **Mostrar el problema** — "El inventario manual es lento y propenso a errores"
3. **Mostrar la solución** — "Detectamos productos por empaque visual, sin RFID ni QR"
4. **Los diferenciadores** — Predicción, heatmap, narración, overlay
5. **Métricas** — Precisión del modelo, latencia de actualización, # de productos detectados
6. **Escalabilidad** — "Se puede escalar a N cámaras y N anaqueles"
