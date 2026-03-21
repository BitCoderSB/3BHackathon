# ============================================
# Setup Frontend — Hackathon Tiendas 3B
# Ejecutar desde la raíz del proyecto: .\scripts\setup-frontend.ps1
# ============================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Setup Frontend — Dashboard React 3B" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Verificar Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js no encontrado. Instala Node.js 18+ desde https://nodejs.org" -ForegroundColor Red
    exit 1
}

$nodeVersion = node --version
Write-Host "Node.js encontrado: $nodeVersion" -ForegroundColor Green

# Verificar npm
$npmVersion = npm --version
Write-Host "npm encontrado: v$npmVersion" -ForegroundColor Green

# Instalar dependencias del frontend
Write-Host "`nInstalando dependencias del frontend..." -ForegroundColor Yellow
Push-Location frontend
npm install

# Inicializar Vite + React + TypeScript si no existe vite.config
if (-not (Test-Path "vite.config.ts")) {
    Write-Host "`nInicializando proyecto Vite + React + TypeScript..." -ForegroundColor Yellow
    # Crear vite.config.ts
    @"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/socket.io': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
  },
})
"@ | Set-Content -Path "vite.config.ts" -Encoding UTF8
}

# Crear tsconfig si no existe
if (-not (Test-Path "tsconfig.json")) {
    @"
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
"@ | Set-Content -Path "tsconfig.json" -Encoding UTF8
}

# Crear tailwind.config.js si no existe
if (-not (Test-Path "tailwind.config.js")) {
    @"
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
"@ | Set-Content -Path "tailwind.config.js" -Encoding UTF8
}

# Crear postcss.config.js si no existe
if (-not (Test-Path "postcss.config.js")) {
    @"
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"@ | Set-Content -Path "postcss.config.js" -Encoding UTF8
}

# Crear estructura base src/ si no existe
if (-not (Test-Path "src")) {
    New-Item -ItemType Directory -Path "src" -Force | Out-Null
}

if (-not (Test-Path "src\index.css")) {
    @"
@tailwind base;
@tailwind components;
@tailwind utilities;
"@ | Set-Content -Path "src\index.css" -Encoding UTF8
}

if (-not (Test-Path "index.html")) {
    @"
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Inventario Tiempo Real — Tiendas 3B</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"@ | Set-Content -Path "index.html" -Encoding UTF8
}

Pop-Location

Write-Host "`n✅ Frontend listo!" -ForegroundColor Green
Write-Host "Para iniciar dev server: cd frontend; npm run dev" -ForegroundColor Gray
Write-Host "Dashboard en: http://localhost:3000" -ForegroundColor Gray
