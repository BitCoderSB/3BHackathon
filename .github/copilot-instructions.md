# Copilot Instructions — Hackathon Tiendas 3B

## Proyecto: Inventario en Tiempo Real con Visión por Computadora

### Contexto del Hackathon
Estamos construyendo un sistema que **detecta el retiro de productos de un anaquel** usando visión por computadora (YOLOv8-seg), **actualiza el inventario en tiempo real**, y lo muestra en un **dashboard interactivo con alertas y predicciones**.

### Restricciones del reto
- NO usar QR, RFID, etiquetas ni sensores adicionales
- La clasificación debe ser por **empaque visual** (no por posición)
- Demo en vivo con cámara real
- 7 productos, 1 anaquel, ~8 unidades por SKU

### Stack tecnológico
- **Backend:** Python 3.11+ / FastAPI / WebSocket / Uvicorn
- **CV/IA:** Ultralytics YOLOv8-seg / OpenCV / NumPy
- **Frontend:** React 18+ / Vite / TailwindCSS / Recharts / Socket.IO client
- **Comunicación:** WebSocket (socket.io) para tiempo real, REST para consultas
- **BD:** SQLite o en memoria (dict/list) — hackathon, priorizar velocidad

### Estructura del proyecto
```
3B/
├── .github/copilot-instructions.md   ← ESTE ARCHIVO (instrucciones globales)
├── assets/                            ← Insumos del hackathon (NO modificar)
│   ├── project-7-.../images/          ← 71 imágenes etiquetadas del anaquel
│   ├── project-7-.../labels/          ← Labels YOLO (polígono/segmentación)
│   ├── project-7-.../classes.txt      ← 7 clases: agua_burst, burst_energetica_roja, etc.
│   ├── productosdelanaquel.md         ← JSON con 7 productos del anaquel
│   ├── Hackaton-datos_productos.csv   ← CSV con datos extendidos
│   └── cadenadeconexion.md            ← RTSP URLs de cámaras
├── backend/                           ← Python: FastAPI + CV + lógica
├── frontend/                          ← React: Dashboard
├── models/                            ← Modelos YOLO entrenados (.pt)
├── scripts/                           ← Scripts de setup y utilidades
├── analisis-reto-inventario.md        ← Análisis del reto
└── mvp-requisitos-y-dependencias.md   ← Requisitos, contratos, dependencias
```

### Los 7 productos del anaquel (clases YOLO)
| ID | Clase | Producto |
|---|---|---|
| 0 | agua_burst | Agua Natural Burst 1500ml |
| 1 | burst_energetica_roja | Bebida Energetica Red Burst 473ml |
| 2 | burst_energy | Bebida Energetica Original Burst Energy 600ml |
| 3 | nachos_naturasol | Nachos Con Sal Naturasol 200gr |
| 4 | nebraska_mango | Bebida Mango-Durazno Nebraska 460ml |
| 5 | sisi_cola | Refresco Cola Sin Azucar Sisi 355ml |
| 6 | sun_paradise_naranja | Bebida Naranja Sun Paradise 900ml |

### Módulos del sistema
- **M1:** Captura de video (cámara RTSP/USB/video)
- **M2:** Motor CV (YOLOv8-seg detección + conteo + eventos)
- **M3:** Motor inventario (estado, decrementos, alertas)
- **M4:** API Backend (FastAPI REST + WebSocket)
- **M5:** Video overlay (bounding boxes + semáforo)
- **M6:** Modelo predictivo (cuándo se agotará cada SKU)
- **M7:** Heatmap de actividad del anaquel
- **M8:** Narración inteligente (mensajes textuales automáticos)
- **M9:** Dashboard React (consume todo vía WebSocket)

### Reglas para generar código
1. **Velocidad sobre perfección** — Es un hackathon, prioriza código funcional
2. **Respetar contratos** — Las interfaces entre módulos están definidas en `mvp-requisitos-y-dependencias.md`
3. **Usar dataclasses** para modelos de datos en Python
4. **Usar TypeScript types/interfaces** en el frontend
5. **Todo en español** — Nombres de variables y funciones en inglés, comentarios y UI en español
6. **Tipo de labels:** Las anotaciones son YOLO POLYGON (segmentación), usar `task=segment`
7. **Cámaras RTSP** como fuente principal, fallback a cámara USB (índice 0)
8. **No inventar datos** — Usar los productos reales del catálogo
9. **Preferir soluciones simples** — No over-engineer
10. **Mocks** — Si un módulo aún no tiene su dependencia, usar los mocks definidos en contratos
