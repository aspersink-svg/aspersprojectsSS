@echo off
chcp 65001 >nul
title Copiar .exe a htdocs
color 0B

echo ========================================
echo   COPIAR MINECRAFTSSTOOL.EXE A HTDOCS
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
    echo    3. Espera a que se compile el proyecto
    echo.
    pause
    exit /b 1
)

:: Copiar a htdocs
echo.
echo 📋 Copiando archivo a htdocs...
set "TARGET_PATH=C:\xampp\htdocs\minecraft-ss-tool\MinecraftSSTool.exe"

copy "%EXE_PATH%" "%TARGET_PATH%" >nul

if %errorlevel% equ 0 (
    echo ✅ Archivo copiado exitosamente a:
    echo    %TARGET_PATH%
    echo.
    echo 🌐 La descarga ahora funcionará correctamente
) else (
    echo ❌ Error copiando el archivo
    echo    Verifica que tengas permisos de escritura
)

echo.
pause
