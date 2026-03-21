# ============================================
# Setup Backend — Hackathon Tiendas 3B
# Ejecutar desde la raíz del proyecto: .\scripts\setup-backend.ps1
# ============================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Setup Backend — Inventario Tiempo Real 3B" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Verificar Python
$pythonCmd = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
             elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" }
             else { $null }

if (-not $pythonCmd) {
    Write-Host "ERROR: Python no encontrado. Instala Python 3.11+ desde https://python.org" -ForegroundColor Red
    exit 1
}

$version = & $pythonCmd --version 2>&1
Write-Host "Python encontrado: $version" -ForegroundColor Green

# Crear entorno virtual
$venvPath = "backend\.venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "`nCreando entorno virtual en $venvPath..." -ForegroundColor Yellow
    & $pythonCmd -m venv $venvPath
} else {
    Write-Host "`nEntorno virtual ya existe en $venvPath" -ForegroundColor Green
}

# Activar entorno virtual
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & $activateScript
} else {
    Write-Host "ERROR: No se pudo activar el entorno virtual" -ForegroundColor Red
    exit 1
}

# Instalar dependencias
Write-Host "`nInstalando dependencias de Python..." -ForegroundColor Yellow
pip install -r backend\requirements.txt

# Verificar instalaciones críticas
Write-Host "`n--- Verificación ---" -ForegroundColor Cyan
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import cv2; print(f'OpenCV {cv2.__version__}')"
python -c "import ultralytics; print(f'Ultralytics {ultralytics.__version__}')"
python -c "import socketio; print(f'python-socketio OK')"

Write-Host "`n✅ Backend listo!" -ForegroundColor Green
Write-Host "Para activar el entorno: .\backend\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "Para iniciar el servidor: cd backend; uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
