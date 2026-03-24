#!/bin/bash
# ============================================
# Setup Completo — Hackathon Tiendas 3B
# Ejecutar desde la raíz del proyecto: ./scripts/setup-all.sh
# ============================================

# Definir colores
BLUE='\033[34m'
CYAN='\033[36m'
MAGENTA='\033[35m'
GREEN='\033[32m'
GRAY='\033[90m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}  ██████╗ ██████╗     ██╗███╗   ██╗██╗   ██╗${NC}"
echo -e "${BLUE}  ╚════██╗██╔══██╗    ██║████╗  ██║██║   ██║${NC}"
echo -e "${BLUE}   █████╔╝██████╔╝    ██║██╔██╗ ██║██║   ██║${NC}"
echo -e "${BLUE}   ╚═══██╗██╔══██╗    ██║██║╚██╗██║╚██╗ ██╔╝${NC}"
echo -e "${BLUE}  ██████╔╝██████╔╝    ██║██║ ╚████║ ╚████╔╝ ${NC}"
echo -e "${BLUE}  ╚═════╝ ╚═════╝     ╚═╝╚═╝  ╚═══╝  ╚═══╝ ${NC}"
echo -e "${CYAN}  Inventario en Tiempo Real con Vision por Computadora${NC}"
echo ""

# Obtener la ruta del directorio del script actual
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo -e "${MAGENTA}=== PASO 1/2: Backend (Python) ===${NC}"
bash "$DIR/setup-backend.sh"

echo ""
echo -e "${MAGENTA}=== PASO 2/2: Frontend (React) ===${NC}"
bash "$DIR/setup-frontend.sh"

echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  ✅ TODO LISTO — Ambiente configurado${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo -e "${CYAN}Comandos rápidos:${NC}"
echo -e "${GRAY}  Backend:  source backend/.venv/bin/activate; cd backend; uvicorn main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo -e "${GRAY}  Frontend: cd frontend; npm run dev${NC}"
echo -e "${GRAY}  Dashboard: http://localhost:3000${NC}"
echo -e "${GRAY}  API Docs:  http://localhost:8000/docs${NC}"
