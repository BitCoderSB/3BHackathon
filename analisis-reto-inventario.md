# 🏪 Análisis del Reto — Inventario en Tiempo Real con Visión por Computadora

## Hackathon Tiendas 3B

---

## 1. Resumen del Reto

| Aspecto | Detalle |
|---|---|
| **Objetivo** | Detectar retiro de productos del anaquel mediante visión por computadora y actualizar inventario en tiempo real |
| **Anaquel** | 1 anaquel monitoreado con cámara fija (5 MPX) |
| **SKUs** | 7 productos distintos con slots fijos |
| **Stock inicial** | ~8 unidades por SKU |
| **Restricciones** | Sin QR, RFID, etiquetas ni sensores. Clasificación por empaque obligatoria (no solo posición) |
| **Alerta** | Umbral configurable (default 20%) |
| **Demo** | En vivo, sin intervención manual |

### Criterios de Evaluación

| Criterio | Peso |
|---|---|
| Funcionalidad (precisión y estabilidad) | **40%** |
| Simplicidad e Innovación | **30%** |
| UI/UX (Dashboard) | **20%** |
| Pitch | **10%** |

> **Insight clave:** Innovación + Simplicidad pesa el **30%**. No se trata solo de que funcione, sino de que sea creativo y elegante. Aquí es donde podemos diferenciarnos.

---

## 2. Análisis de la Problemática Real

### ¿Qué sucede en la operación actual?
- El inventario teórico (basado en ventas POS y reposiciones) diverge del inventario físico real.
- No hay visibilidad de lo que pasa **entre** el anaquel y la caja registradora.
- Los quiebres de stock pasan desapercibidos hasta que alguien reporta o un cliente se va.

### ¿Qué se espera resolver?
- **Cerrar la brecha** entre inventario teórico y real en el punto del anaquel.
- Dar **visibilidad en tiempo real** del estado del anaquel.
- Generar **alertas proactivas** para reposición.

---

## 3. Arquitectura Propuesta (Base Sólida)

```
┌──────────────┐    WebSocket/SSE     ┌──────────────────┐
│  Cámara 5MPX │──── frames ────────▶ │  Backend (Python) │
│  (USB/IP)    │                      │                    │
└──────────────┘                      │  ┌──────────────┐  │
                                      │  │ Motor CV     │  │ ◄── YOLOv8/v11 + Tracking
                                      │  │ (Detección)  │  │
                                      │  └──────┬───────┘  │
                                      │         │          │
                                      │  ┌──────▼───────┐  │
                                      │  │ Motor de     │  │ ◄── Lógica de decremento
                                      │  │ Inventario   │  │     (anti false-positive)
                                      │  └──────┬───────┐  │
                                      │         │          │
                                      │  ┌──────▼───────┐  │
                                      │  │ API REST +   │  │ ◄── FastAPI + WebSocket
                                      │  │ WebSocket    │  │
                                      │  └──────────────┘  │
                                      └────────┬───────────┘
                                               │
                                      ┌────────▼───────────┐
                                      │  Dashboard (React)  │ ◄── Tiempo real, alertas
                                      │  + Módulo           │     visuales, predicción
                                      │    Predictivo       │
                                      └─────────────────────┘
```

### Stack Recomendado

| Capa | Tecnología | Justificación |
|---|---|---|
| **CV / IA** | YOLOv8 o YOLOv11 (Ultralytics) | Detección de objetos en tiempo real, fácil de entrenar con pocas imágenes, soporte de tracking integrado |
| **Backend** | Python + FastAPI | Ecosistema ML nativo, async, WebSocket nativo, rápido de desarrollar |
| **Frontend** | React + TailwindCSS + Recharts | UI moderna, responsive, gráficas en tiempo real |
| **Comunicación** | WebSocket (Socket.IO) | Latencia mínima para actualizaciones en tiempo real |
| **BD** | SQLite o Redis | Ligero, sin infraestructura extra, ideal para MVP y demo en vivo |

---

## 4. 💡 Ideas Innovadoras y Diferenciadoras

### 4.1 🧠 Modelo Predictivo de Desabasto (Diferenciador #1)

**Concepto:** No solo informar el estado actual del inventario, sino **predecir cuándo se agotará cada SKU** basándose en la velocidad de retiro observada.

**Implementación:**
- Registrar cada evento de retiro con timestamp.
- Calcular la **tasa de retiro por SKU** (unidades/hora) con ventana deslizante.
- Aplicar **regresión lineal simple** o **suavizado exponencial** para proyectar el tiempo estimado de agotamiento.
- Mostrar en dashboard: `"Producto X se agotará en ~45 minutos al ritmo actual"`.

```python
# Ejemplo simplificado del modelo predictivo
import numpy as np
from datetime import datetime, timedelta

def predecir_agotamiento(eventos_retiro: list[datetime], stock_actual: int) -> timedelta:
    """Predice en cuánto tiempo se agotará el producto."""
    if len(eventos_retiro) < 2:
        return None  # Insuficientes datos

    # Calcular intervalos entre retiros (en minutos)
    intervalos = [
        (eventos_retiro[i+1] - eventos_retiro[i]).total_seconds() / 60
        for i in range(len(eventos_retiro) - 1)
    ]

    # Suavizado exponencial (da más peso a retiros recientes)
    alpha = 0.3
    tasa_suavizada = intervalos[0]
    for intervalo in intervalos[1:]:
        tasa_suavizada = alpha * intervalo + (1 - alpha) * tasa_suavizada

    # Proyección
    minutos_restantes = tasa_suavizada * stock_actual
    return timedelta(minutes=minutos_restantes)
```

**Valor para 3B:** Permite al personal de tienda priorizar reposición antes de que ocurra el quiebre.

---

### 4.2 🔥 Heatmap de Actividad por Slot (Diferenciador #2)

**Concepto:** Generar un **mapa de calor del anaquel** que visualice qué productos tienen mayor demanda/actividad.

**Implementación:**
- Acumular las detecciones por zona (slot) del anaquel.
- Representar visualmente con gradiente de colores (frío → caliente) las zonas de mayor interacción.
- Actualizar cada N segundos en el dashboard.

**Valor para 3B:** Insights sobre comportamiento del cliente en anaquel. ¿Qué productos atraen más manos? ¿Hay patrones por hora?

---

### 4.3 🎯 Sistema de Detección con Doble Validación (Anti False-Positive)

**Concepto:** En lugar de decrementar con una sola detección, implementar un sistema de **doble confirmación** que reduce falsos positivos drásticamente.

**Implementación — Pipeline de Validación:**

```
Frame N:   Detectar todos los productos visibles → Snapshot A
           ↓
           Detectar mano/interacción en zona de slot
           ↓
Frame N+K: Detectar productos visibles → Snapshot B
           ↓
           Comparar: Si Snapshot B tiene 1 menos de SKU X que Snapshot A
           → Confirmar retiro de SKU X → Decrementar inventario
```

**Técnicas complementarias:**
1. **Conteo por slot:** Entrenar YOLO para detectar cada instancia del producto. Si el conteo baja de 5 a 4 → retiro confirmado.
2. **Detección de mano:** Usar MediaPipe Hands o un modelo adicional para detectar la presencia de una mano en la zona del anaquel como trigger.
3. **Zona de exclusión temporal:** Después de decrementar un SKU, aplicar un cooldown de N segundos para evitar decrementos duplicados.

---

### 4.4 📊 Dashboard con "Narración Inteligente" (Diferenciador #3)

**Concepto:** El dashboard no solo muestra números, sino que **genera texto descriptivo automático** sobre el estado del inventario.

**Ejemplos de narración:**
- `"⚠️ El producto Coca-Cola 600ml ha tenido 3 retiros en los últimos 5 minutos. A este ritmo, se agotará antes de las 3:00 PM."`
- `"✅ Todos los productos están por encima del umbral de seguridad."`
- `"🔴 ALERTA: Galletas Marías alcanzó el umbral crítico (20%). Se recomienda reposición inmediata."`

**Implementación:**
- Reglas de negocio simples que generan templates de texto según condiciones.
- Opcionalmente, usar un LLM local pequeño o API para generar resúmenes más naturales.

---

### 4.5 📹 Feed de Video con Overlay Aumentado (Diferenciador #4)

**Concepto:** Mostrar el video en vivo en el dashboard con **bounding boxes, etiquetas de producto y conteo superpuesto** directamente sobre cada slot.

**Implementación:**
- Enviar frames procesados (con anotaciones de YOLO) al frontend via WebSocket como MJPEG stream o frames base64.
- Superponer información como:
  - Nombre del SKU detectado
  - Conteo actual en el slot
  - Indicador visual (verde/amarillo/rojo) según nivel de stock
  - Animación de "flash" cuando se detecta un retiro

**Valor:** Los jueces ven la detección funcionando en tiempo real. Es extremadamente impactante visualmente.

---

### 4.6 🔄 Sistema de "Undo" Inteligente (Diferenciador #5)

**Concepto:** Si la cámara detecta que alguien **devuelve** un producto al anaquel, **incrementar** el inventario.

**Implementación:**
- Misma lógica de conteo: si Snapshot B tiene MÁS de un SKU que Snapshot A → producto devuelto → incrementar.
- Indicar en el log: `"Producto X fue devuelto al slot 3. Inventario ajustado: 5 → 6."`

**Valor para 3B:** Inventario bidireccional, más preciso que un simple decremento.

---

### 4.7 🎨 Diseño de Dashboard Multi-Vista

**Vista 1 — Panel Operativo (para empleado de tienda):**
```
┌─────────────────────────────────────────────────────┐
│  🏪 Anaquel Inteligente — Tiendas 3B               │
├────────────┬────────────────────────────────────────┤
│            │  📦 Stock en Tiempo Real               │
│  📹 Video │  ┌──────┬──────┬──────┬──────┐        │
│    Feed    │  │ SKU1 │ SKU2 │ SKU3 │ SKU4 │        │
│    con     │  │ ████ │ ██░░ │ █░░░ │ ████ │        │
│  Overlay   │  │  8   │  5   │  2⚠  │  7   │        │
│            │  ├──────┼──────┼──────┤──────┤        │
│            │  │ SKU5 │ SKU6 │ SKU7 │      │        │
│            │  │ ███░ │ ████ │ ██░░ │      │        │
│            │  │  6   │  8   │  4   │      │        │
│            │  └──────┴──────┴──────┘──────┘        │
├────────────┴────────────────────────────────────────┤
│  📝 Log de Eventos                                  │
│  14:32:01 — SKU3 (Galletas) retirado. Stock: 2 ⚠️  │
│  14:31:45 — SKU2 (Coca-Cola) retirado. Stock: 5    │
│  14:30:12 — SKU7 (Jabón) retirado. Stock: 4        │
├─────────────────────────────────────────────────────┤
│  🔮 Predicción: SKU3 se agotará en ~20 min         │
│  🗺️ [Ver Heatmap] [Ver Tendencias] [Configurar]    │
└─────────────────────────────────────────────────────┘
```

**Vista 2 — Analítica (para gerente/juez):**
- Gráfica de líneas: evolución del stock por SKU en el tiempo.
- Heatmap del anaquel.
- Tabla con métricas: tasa de retiro/hora, predicción de agotamiento, precisión del modelo.
- Timeline de eventos con filtros.

---

## 5. 🛠️ Plan de Implementación por Etapas

### Etapa 1 — Core CV (Prioridad Absoluta)
- [ ] Etiquetar dataset con fotos proporcionadas (Roboflow o LabelImg)
- [ ] Entrenar YOLOv8/v11 para detectar los 7 SKUs
- [ ] Implementar captura de video en tiempo real (OpenCV)
- [ ] Pipeline: detección → conteo por slot → lógica de decremento
- [ ] Sistema anti-falsos positivos (cooldown + doble validación)

### Etapa 2 — Backend + API
- [ ] FastAPI con endpoints REST + WebSocket
- [ ] Motor de inventario (estado, decrementos, alertas)
- [ ] Endpoint `/ws/inventory` para stream de datos en tiempo real
- [ ] Endpoint `/api/inventory` para consulta REST
- [ ] Endpoint `/api/events` para historial de eventos

### Etapa 3 — Dashboard
- [ ] Layout principal con video feed + panel de stock
- [ ] Barras/indicadores visuales por SKU con colores semáforo
- [ ] Alertas visuales (toast/banner) al alcanzar umbral
- [ ] Log de eventos en tiempo real
- [ ] Conexión WebSocket con backend

### Etapa 4 — Diferenciadores (Innovación)
- [ ] Modelo predictivo de agotamiento
- [ ] Heatmap de actividad del anaquel
- [ ] Narración inteligente del estado
- [ ] Video con overlay aumentado
- [ ] Detección de devolución (incremento)

---

## 6. ⚡ Tips para la Demo en Vivo

1. **Tener un plan B:** Si YOLO falla, tener un modo semi-manual de respaldo.
2. **Calibrar iluminación:** Probar con diferentes condiciones de luz antes.
3. **Precargar el modelo:** El primer inference de YOLO es lento. Hacer un "warm-up" antes de la demo.
4. **Cooldown agresivo:** Mejor perder un retiro que decrementar doble.
5. **Log visible:** Que los jueces vean cada decisión del sistema en pantalla.
6. **Umbral de confianza alto:** Usar confidence threshold de 0.7+ para evitar falsos positivos.

---

## 7. 🎤 Estructura del Pitch Sugerida

| Tiempo | Contenido |
|---|---|
| 0:00 - 0:30 | **El problema:** "En Tiendas 3B, el inventario teórico y el real no coinciden. Cada quiebre de stock es una venta perdida." |
| 0:30 - 1:30 | **La solución:** Visión por computadora + inventario en tiempo real. Explicar flujo end-to-end con diagrama. |
| 1:30 - 3:00 | **Demo en vivo:** Retirar productos, mostrar detección, decremento, alerta, predicción. |
| 3:00 - 4:00 | **Innovación:** Modelo predictivo, heatmap, devolución, narración inteligente. |
| 4:00 - 4:30 | **Valor para 3B:** Reducción de quiebres, reposición proactiva, datos de comportamiento. |

---

## 8. 🔑 Factores Críticos de Éxito

| Factor | Estrategia |
|---|---|
| **Precisión de detección** | Dataset bien etiquetado + data augmentation + fine-tuning |
| **Evitar falsos positivos** | Doble validación + cooldown + umbral de confianza alto |
| **Estabilidad en demo** | Pruebas extensivas + warm-up del modelo + plan B |
| **Impacto visual** | Video con overlay + dashboard atractivo + animaciones sutiles |
| **Diferenciación** | Modelo predictivo + heatmap + devolución + narración |

---

## 9. Tecnologías Clave y Referencias Rápidas

| Herramienta | Uso | Link |
|---|---|---|
| **Ultralytics YOLOv8** | Detección de objetos | `pip install ultralytics` |
| **Roboflow** | Etiquetado y augmentation | roboflow.com |
| **FastAPI** | Backend async | `pip install fastapi uvicorn` |
| **OpenCV** | Captura y procesamiento de video | `pip install opencv-python` |
| **React + Vite** | Frontend rápido | `npm create vite@latest` |
| **Socket.IO** | WebSocket bidireccional | `pip install python-socketio` |
| **Recharts** | Gráficas en React | `npm install recharts` |
| **TailwindCSS** | Estilos rápidos | `npm install tailwindcss` |

---

> **Nota final:** La clave para ganar no es solo que funcione, sino que sea **visualmente impactante**, **inteligente en sus decisiones** y **cuente una historia clara**. El 30% de innovación + 20% de UI/UX = 50% del puntaje depende de cómo se ve y qué tan creativo es. Inviertan tiempo en la experiencia visual y los diferenciadores tanto como en el modelo de CV.
