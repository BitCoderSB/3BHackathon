<p align="center">
  <img src="https://img.shields.io/badge/hackathon-Tiendas%203B-blue?style=for-the-badge" alt="Hackathon Tiendas 3B"/>
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/react-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/YOLOv8-seg-FF6F00?style=for-the-badge&logo=pytorch&logoColor=white" alt="YOLOv8"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
</p>

<h1 align="center">🏪 Anaquel Inteligente — Tiendas 3B</h1>

<p align="center">
  <b>Inventario en tiempo real con Visión por Computadora</b><br/>
  Sistema que detecta el retiro y devolución de productos de un anaquel usando YOLOv8 segmentation,<br/>
  actualiza el inventario al instante y lo visualiza en un dashboard interactivo con alertas y predicciones.
</p>

<p align="center">
  <a href="https://hackaton3b.com/reto-inventario.html">🔗 Página del reto</a>
</p>

---

## 📋 El Problema

En la operación diaria de Tiendas 3B, el inventario teórico (basado en ventas POS y reposiciones) **diverge del inventario físico real** en el anaquel. No hay visibilidad de lo que sucede entre el estante y la caja registradora: los quiebres de stock pasan desapercibidos hasta que un cliente se va sin comprar.

## 💡 Nuestra Solución

Una cámara fija apunta al anaquel. Un modelo de **segmentación YOLOv8** entrenado con imágenes reales de los productos identifica y cuenta cada SKU frame a frame. Cuando detecta que un producto fue retirado (o devuelto), actualiza el inventario en tiempo real y notifica al dashboard vía **WebSocket**.

**Sin QR. Sin RFID. Sin sensores.** Solo visión por computadora.

---

## ✨ Funcionalidades Principales

| Módulo | Descripción |
|--------|-------------|
| 🎥 **Captura de Video** | Conexión RTSP / USB / video pregrabado con fallback automático |
| 🧠 **Motor de Visión (YOLOv8-seg)** | Detección por instancia + conteo por slot + doble validación anti falsos positivos |
| 📦 **Motor de Inventario** | Estado en tiempo real, decrementos/incrementos, alertas por umbral (20%) |
| 🔌 **API Backend** | FastAPI REST + WebSocket (Socket.IO) para comunicación en tiempo real |
| 📹 **Video Overlay** | Feed en vivo con bounding boxes, etiquetas, conteo y semáforo de stock |
| 🔮 **Modelo Predictivo** | Estima cuándo se agotará cada SKU basándose en la velocidad de retiro |
| 🔥 **Heatmap** | Mapa de calor del anaquel: qué zonas tienen mayor actividad |
| 📝 **Narración Inteligente** | Genera mensajes automáticos sobre el estado del inventario |
| 🎨 **Dashboard React** | Panel operativo y analítico en tiempo real |

---

## 🏗️ Arquitectura

```
┌──────────────┐                      ┌──────────────────────────┐
│  📷 Cámara   │──── frames ────────▶ │     Backend (Python)     │
│  RTSP / USB  │                      │                          │
└──────────────┘                      │  ┌────────────────────┐  │
                                      │  │ YOLOv8-seg         │  │  Detección + Conteo
                                      │  │ Motor de Visión    │  │
                                      │  └─────────┬──────────┘  │
                                      │            │             │
                                      │  ┌─────────▼──────────┐  │
                                      │  │ Motor de           │  │  Inventario + Alertas
                                      │  │ Inventario         │  │
                                      │  └─────────┬──────────┘  │
                                      │            │             │
                                      │  ┌─────────▼──────────┐  │
                                      │  │ Predicción         │  │  Agotamiento estimado
                                      │  │ Heatmap            │  │  Mapa de actividad
                                      │  │ Narración          │  │  Mensajes automáticos
                                      │  └─────────┬──────────┘  │
                                      │            │             │
                                      │  ┌─────────▼──────────┐  │
                                      │  │ FastAPI + Socket.IO │  │  REST + WebSocket
                                      │  └─────────┬──────────┘  │
                                      └────────────┼─────────────┘
                                                   │
                                      ┌────────────▼─────────────┐
                                      │   🎨 Dashboard (React)   │
                                      │   Vite + TailwindCSS     │
                                      │   Recharts + Socket.IO   │
                                      └──────────────────────────┘
```

---

## 🛒 Productos del Anaquel

El sistema detecta y monitorea **7 productos reales** de marcas propias de Tiendas 3B:

| # | Producto | Presentación | Categoría |
|---|----------|-------------|-----------|
| 0 | 💧 Agua Natural Burst | 1500 ml | Water |
| 1 | ⚡ Bebida Energética Red Burst | 473 ml | Beverages |
| 2 | ⚡ Bebida Energética Original Burst Energy | 600 ml | Beverages |
| 3 | 🌽 Nachos Con Sal Naturasol | 200 gr | Snacks |
| 4 | 🥭 Bebida Mango-Durazno Nebraska | 460 ml | Beverages |
| 5 | 🥤 Refresco Cola Sin Azúcar Sisi | 355 ml | Beverages |
| 6 | 🍊 Bebida Naranja Sun Paradise | 900 ml | Beverages |

---

## 🖥️ Dashboard

El dashboard cuenta con 4 vistas principales:

| Vista | Descripción |
|-------|-------------|
| **📊 Panel en Vivo** | Video feed con overlay + stock en tiempo real + log de eventos + predicciones |
| **📦 Catálogo de Productos** | Detalle de cada SKU con métricas e información del producto |
| **📈 Analítica** | Gráficas de tendencia de stock, heatmap del anaquel, métricas de rendimiento |
| **📋 Actividad** | Timeline completo de eventos con filtros |

---

## 🚀 Inicio Rápido

### Prerrequisitos

- **Python** 3.11+
- **Node.js** 18+
- **Git**

### 1. Clonar el repositorio

```bash
git clone https://github.com/BitCoderSB/3BHackathon.git
cd 3BHackathon
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Ejecutar

**Backend** (terminal 1):
```bash
cd backend
python main.py
```

**Frontend** (terminal 2):
```bash
cd frontend
npm run dev
```

El dashboard estará disponible en `http://localhost:5173` y el backend en `http://localhost:8000`.

---

## 🧪 Entrenamiento del Modelo

El dataset incluye **71 imágenes etiquetadas** del anaquel real con anotaciones YOLO en formato polígono (segmentación).

```bash
cd backend
python train_model.py
```

Los modelos entrenados se guardan en `models/` y `runs/`.

---

## 📁 Estructura del Proyecto

```
3BHackathon/
├── 📂 assets/                    # Insumos del hackathon
│   ├── images/                   # 71 imágenes etiquetadas del anaquel
│   ├── labels/                   # Labels YOLO (polígono/segmentación)
│   ├── classes.txt               # 7 clases de productos
│   ├── productosdelanaquel.md    # Catálogo JSON de productos
│   └── Hackaton-datos_productos.csv
│
├── 📂 backend/                   # Python: FastAPI + CV + Lógica
│   ├── main.py                   # Servidor principal (FastAPI + Socket.IO)
│   ├── camera_capture.py         # M1: Captura de video
│   ├── detection_engine.py       # M2: Motor YOLOv8-seg
│   ├── inventory_engine.py       # M3: Motor de inventario
│   ├── prediction_engine.py      # M6: Modelo predictivo
│   ├── heatmap_engine.py         # M7: Heatmap de actividad
│   ├── narrative_engine.py       # M8: Narración inteligente
│   ├── video_overlay.py          # M5: Video con overlay
│   ├── contracts.py              # Contratos/tipos compartidos
│   └── train_model.py            # Script de entrenamiento YOLO
│
├── 📂 frontend/                  # React: Dashboard
│   └── src/
│       ├── App.tsx               # Router principal
│       ├── components/           # Layout, Sidebar, VideoFeed
│       ├── pages/                # LivePanel, ProductCatalog, Analytics, Activity
│       ├── hooks/                # useSocket (conexión WebSocket)
│       └── types/                # Interfaces TypeScript
│
├── 📂 models/                    # Modelos YOLO entrenados (.pt)
├── 📂 runs/                      # Resultados de entrenamientos
└── 📂 scripts/                   # Scripts de setup
```

---

## 🛠️ Stack Tecnológico

<table>
  <tr>
    <th>Capa</th>
    <th>Tecnología</th>
  </tr>
  <tr>
    <td><b>CV / IA</b></td>
    <td>Ultralytics YOLOv8-seg · OpenCV · NumPy</td>
  </tr>
  <tr>
    <td><b>Backend</b></td>
    <td>Python 3.11 · FastAPI · Uvicorn · python-socketio</td>
  </tr>
  <tr>
    <td><b>Frontend</b></td>
    <td>React 18 · TypeScript · Vite · TailwindCSS · Recharts · Socket.IO Client</td>
  </tr>
  <tr>
    <td><b>Comunicación</b></td>
    <td>WebSocket (Socket.IO) para tiempo real · REST para consultas</td>
  </tr>
  <tr>
    <td><b>Datos</b></td>
    <td>En memoria (optimizado para velocidad en demo)</td>
  </tr>
</table>

---

## 🎯 Criterios de Evaluación del Hackathon

| Criterio | Peso |
|----------|------|
| Funcionalidad (precisión y estabilidad) | **40%** |
| Simplicidad e Innovación | **30%** |
| UI/UX (Dashboard) | **20%** |
| Pitch | **10%** |

---

## 🔑 Diferenciadores Clave

- **🔮 Predicción de desabasto** — No solo muestra el estado actual, sino cuándo se agotará cada producto al ritmo de retiro observado.
- **🔥 Heatmap de actividad** — Visualiza qué zonas del anaquel tienen mayor demanda.
- **🔄 Detección bidireccional** — Detecta tanto retiros como devoluciones de productos.
- **📝 Narración inteligente** — El sistema genera mensajes descriptivos automáticos sobre el estado del inventario.
- **📹 Video con overlay aumentado** — Feed en vivo con bounding boxes, conteo y semáforo visual directamente sobre el anaquel.
- **🛡️ Anti falsos positivos** — Doble validación + cooldown para asegurar precisión en la detección.

---

## 👥 Equipo

Proyecto desarrollado para el **Hackathon Tiendas 3B 2026**.

| Integrante |
|------------|
| Aldair Iglesias Hernández |
| Carlos Alberto Sánchez Bonilla |
| Christopher Daza Herrera |
| José Guadalupe Zacarías Silberio |
| Luis Alberto González Muñoz |

---

<p align="center">
  <sub>Hecho con ❤️ para el Hackathon Tiendas 3B 2026</sub>
</p>
