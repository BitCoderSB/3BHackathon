# ============================================
# Setup Completo — Hackathon Tiendas 3B
# Ejecutar desde la raíz del proyecto: .\scripts\setup-all.ps1
# ============================================

Write-Host ""
Write-Host "  ██████╗ ██████╗     ██╗███╗   ██╗██╗   ██╗" -ForegroundColor Blue
Write-Host "  ╚════██╗██╔══██╗    ██║████╗  ██║██║   ██║" -ForegroundColor Blue
Write-Host "   █████╔╝██████╔╝    ██║██╔██╗ ██║██║   ██║" -ForegroundColor Blue
Write-Host "   ╚═══██╗██╔══██╗    ██║██║╚██╗██║╚██╗ ██╔╝" -ForegroundColor Blue
Write-Host "  ██████╔╝██████╔╝    ██║██║ ╚████║ ╚████╔╝ " -ForegroundColor Blue
Write-Host "  ╚═════╝ ╚═════╝     ╚═╝╚═╝  ╚═══╝  ╚═══╝ " -ForegroundColor Blue
Write-Host "  Inventario en Tiempo Real con Vision por Computadora" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== PASO 1/2: Backend (Python) ===" -ForegroundColor Magenta
& "$PSScriptRoot\setup-backend.ps1"

Write-Host ""
Write-Host "=== PASO 2/2: Frontend (React) ===" -ForegroundColor Magenta
& "$PSScriptRoot\setup-frontend.ps1"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "  ✅ TODO LISTO — Ambiente configurado" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Comandos rápidos:" -ForegroundColor Cyan
Write-Host "  Backend:  .\backend\.venv\Scripts\Activate.ps1; cd backend; uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host "  Frontend: cd frontend; npm run dev" -ForegroundColor Gray
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Gray
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Gray
