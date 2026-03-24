#!/bin/bash
# ============================================
# Setup Backend — Hackathon Tiendas 3B
# Ejecutar desde la raíz del proyecto: ./scripts/setup-backend.sh
# ============================================

CYAN='\033[36m'
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
GRAY='\033[90m'
NC='\033[0m'

echo -e "${CYAN}==============================================${NC}"
echo -e "${CYAN}  Setup Backend — Inventario Tiempo Real 3B${NC}"
echo -e "${CYAN}==============================================${NC}"

# Verificar Python (Priorizar python3 en macOS)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}ERROR: Python no encontrado. Instala Python 3.11+ desde https://python.org${NC}"
    exit 1
fi

VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}Python encontrado: $VERSION${NC}"

# Crear entorno virtual
VENV_PATH="backend/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\n${YELLOW}Creando entorno virtual en $VENV_PATH...${NC}"
    $PYTHON_CMD -m venv $VENV_PATH
else
    echo -e "\n${GREEN}Entorno virtual ya existe en $VENV_PATH${NC}"
fi

# Activar entorno virtual
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
if [ -f "$ACTIVATE_SCRIPT" ]; then
    echo -e "${YELLOW}Activando entorno virtual...${NC}"
    source "$ACTIVATE_SCRIPT"
else
    echo -e "${RED}ERROR: No se pudo activar el entorno virtual${NC}"
    exit 1
fi

# Instalar dependencias
echo -e "\n${YELLOW}Instalando dependencias de Python...${NC}"
pip install -r backend/requirements.txt

# Verificar instalaciones críticas
echo -e "\n${CYAN}--- Verificación ---${NC}"
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import cv2; print(f'OpenCV {cv2.__version__}')"
python -c "import ultralytics; print(f'Ultralytics {ultralytics.__version__}')"
python -c "import socketio; print(f'python-socketio OK')"

echo -e "\n${GREEN}✅ Backend listo!${NC}"
echo -e "${GRAY}Para activar el entorno: source backend/.venv/bin/activate${NC}"
echo -e "${GRAY}Para iniciar el servidor: cd backend; uvicorn main:app --reload --host 0.0.0.0 --port 8000${NC}"
