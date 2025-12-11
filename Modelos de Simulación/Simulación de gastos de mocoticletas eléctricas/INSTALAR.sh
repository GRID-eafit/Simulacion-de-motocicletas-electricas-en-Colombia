#!/bin/bash
# Script de instalación rápida para macOS/Linux

echo "=========================================="
echo "Instalación de Simulación de Costos"
echo "=========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "   Por favor instala Python 3.8 o superior"
    exit 1
fi

echo "✓ Python encontrado: $(python3 --version)"
echo ""

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 no está instalado"
    echo "   Por favor instala pip"
    exit 1
fi

echo "✓ pip encontrado"
echo ""

# Instalar dependencias
echo "Instalando dependencias de Python..."
echo ""

pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Instalación completada exitosamente"
    echo "=========================================="
    echo ""
    echo "Puedes ejecutar la simulación con:"
    echo "   python3 calcular_costo_viaje_aleatorio.py"
    echo ""
    echo "O verificar la instalación con:"
    echo "   python3 verificar_instalacion.py"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Error durante la instalación"
    echo "=========================================="
    echo ""
    echo "Si tienes problemas instalando geopandas o fiona,"
    echo "puede que necesites instalar dependencias del sistema:"
    echo ""
    echo "macOS:"
    echo "   brew install gdal"
    echo ""
    echo "Linux (Ubuntu/Debian):"
    echo "   sudo apt-get install gdal-bin libgdal-dev"
    echo ""
    exit 1
fi

