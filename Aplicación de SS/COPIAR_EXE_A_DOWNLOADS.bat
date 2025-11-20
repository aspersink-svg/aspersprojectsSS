@echo off
chcp 65001 >nul
title Copiar .exe a downloads para GitHub
color 0B

echo ========================================
echo   COPIAR MINECRAFTSSTOOL.EXE A DOWNLOADS
echo ========================================
echo.

:: Buscar el archivo .exe
echo 🔍 Buscando MinecraftSSTool.exe...
echo.

set "EXE_FILE="
set "EXE_PATH="

:: Buscar en diferentes ubicaciones
if exist "source\dist\MinecraftSSTool.exe" (
    set "EXE_PATH=source\dist\MinecraftSSTool.exe"
    set "EXE_FILE=MinecraftSSTool.exe"
    echo ✅ Encontrado en: source\dist\
) else if exist "dist\MinecraftSSTool.exe" (
    set "EXE_PATH=dist\MinecraftSSTool.exe"
    set "EXE_FILE=MinecraftSSTool.exe"
    echo ✅ Encontrado en: dist\
) else if exist "MinecraftSSTool.exe" (
    set "EXE_PATH=MinecraftSSTool.exe"
    set "EXE_FILE=MinecraftSSTool.exe"
    echo ✅ Encontrado en: raíz del proyecto
) else (
    echo ❌ No se encontró MinecraftSSTool.exe
    echo.
    echo 💡 Opciones:
    echo    1. Compila el proyecto primero
    echo    2. Busca el archivo .exe manualmente
    echo.
    pause
    exit /b 1
)

:: Crear carpeta downloads si no existe
if not exist "downloads" (
    echo 📁 Creando carpeta downloads...
    mkdir downloads
)

:: Copiar a downloads
echo.
echo 📋 Copiando archivo a downloads...
set "TARGET_PATH=downloads\MinecraftSSTool.exe"

copy "%EXE_PATH%" "%TARGET_PATH%" >nul

if %errorlevel% equ 0 (
    echo ✅ Archivo copiado exitosamente a:
    echo    %TARGET_PATH%
    echo.
    echo 📤 Ahora puedes subir este archivo a GitHub
    echo    El archivo está configurado para subirse al repositorio
    echo.
    echo 💡 Próximos pasos:
    echo    1. Abre GitHub Desktop
    echo    2. Verás el archivo downloads\MinecraftSSTool.exe como nuevo
    echo    3. Haz commit y push
    echo.
) else (
    echo ❌ Error copiando el archivo
    echo    Verifica que tengas permisos de escritura
)

echo.
pause

