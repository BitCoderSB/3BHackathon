"""
Script de entrenamiento YOLOv8-seg para detección de productos del anaquel.
Hackathon Tiendas 3B — Módulo M2 (CV/IA Lead)
"""

import shutil
from pathlib import Path

import torch
from ultralytics import YOLO

# --- Configuración ---
ROOT = Path(__file__).resolve().parent.parent
DATASET_YAML = Path(__file__).resolve().parent / "dataset.yaml"
OUTPUT_MODEL = ROOT / "models" / "best.pt"
BASE_MODEL = "yolov8n-seg.pt"
EPOCHS = 50
IMGSZ = 640
BATCH = 8
#DEVICE = "0" if torch.cuda.is_available() else "cpu"
DEVICE = "mps"


def main():
    print(f"=== Entrenamiento YOLOv8-seg — Anaquel 3B ===")
    print(f"Dataset: {DATASET_YAML}")
    print(f"Modelo base: {BASE_MODEL}")
    print(f"Device: {DEVICE}")
    print(f"Epochs: {EPOCHS}, ImgSize: {IMGSZ}, Batch: {BATCH}")
    print()

    # Cargar modelo base
    model = YOLO(BASE_MODEL)

    # Entrenar
    results = model.train(
        data=str(DATASET_YAML),
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        task="segment",
        name="anaquel_3b",
        project=str(ROOT / "runs"),
    )

    # Copiar mejor modelo a models/best.pt
    OUTPUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    if best_weights.exists():
        shutil.copy2(best_weights, OUTPUT_MODEL)
        print(f"\nModelo guardado en: {OUTPUT_MODEL}")
    else:
        print(f"\nADVERTENCIA: No se encontró {best_weights}")

    # Imprimir métricas
    print("\n=== Métricas de entrenamiento ===")
    metrics = model.val()
    print(f"  mAP50:      {metrics.seg.map50:.4f}")
    print(f"  mAP50-95:   {metrics.seg.map:.4f}")

    # Métricas por clase
    names = metrics.names
    print("\n  Por clase:")
    for i, name in names.items():
        ap50 = metrics.seg.ap50[i] if i < len(metrics.seg.ap50) else 0
        print(f"    {name}: AP50={ap50:.4f}")

    print("\n✅ Entrenamiento completado.")


if __name__ == "__main__":
    main()
