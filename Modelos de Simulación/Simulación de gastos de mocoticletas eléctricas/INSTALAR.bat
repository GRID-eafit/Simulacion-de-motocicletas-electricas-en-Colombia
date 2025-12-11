@echo off
REM Script de instalación rápida para Windows

echo ==========================================
echo Instalacion de Simulacion de Costos
echo ==========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado
    echo Por favor instala Python 3.8 o superior
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version
echo.

REM Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip no esta instalado
    echo Por favor instala pip
    pause
    exit /b 1
)

echo [OK] pip encontrado
echo.

REM Instalar dependencias
echo Instalando dependencias de Python...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Error durante la instalacion
    echo ==========================================
    echo.
    echo Si tienes problemas instalando geopandas o fiona,
    echo puedes necesitar instalar GDAL manualmente.
    echo.
    echo Visita: https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ==========================================
    echo [OK] Instalacion completada exitosamente
    echo ==========================================
    echo.
    echo Puedes ejecutar la simulacion con:
    echo    python calcular_costo_viaje_aleatorio.py
    echo.
    echo O verificar la instalacion con:
    echo    python verificar_instalacion.py
    echo.
    pause
)

