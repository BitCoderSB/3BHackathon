from ultralytics import YOLO

# 1. Cargar el modelo que acabas de entrenar
model_path = '/Users/josezacarias/Hackaton3B-Reto1/models/best.pt'
model = YOLO(model_path)

# 2. Ruta a una foto NUEVA de un anaquel (que no esté en tus 70 originales)
# Cambia esta ruta por la de tu foto de prueba
image_to_test = '/Users/josezacarias/Documents/test3.png'

# 3. Correr la predicción
# show=True abrirá una ventana para mostrarte el resultado.
# save=True guardará la imagen con las máscaras dibujadas en una carpeta "runs/predict"
results = model.predict(source=image_to_test, save=True, show=True, conf=0.15) 

print("¡Predicción terminada! Revisa la carpeta runs/predict/")
