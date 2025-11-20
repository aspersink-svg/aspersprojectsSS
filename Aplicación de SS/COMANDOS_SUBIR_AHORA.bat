@echo off
chcp 65001 >nul
title Subir Archivos a GitHub - Solución Rápida
color 0A

echo ========================================
echo   SUBIR ARCHIVOS A GITHUB
echo ========================================
echo.

:: Verificar que estamos en un repositorio Git
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  No se detectó un repositorio Git en esta carpeta
    echo.
    echo 💡 Si usas GitHub Desktop:
    echo    1. Abre GitHub Desktop
    echo    2. Ve a Repository → Open in Command Prompt
    echo    3. Ejecuta este script desde ahí
    echo.
    echo 💡 O ejecuta estos comandos manualmente:
    echo    git add -f source/dist/MinecraftSSTool.exe
    echo    git add -f source/build/
    echo    git add -f source/dist/
    echo    git commit -m "Agregar ejecutable y carpetas"
    echo    git push
    echo.
    pause
    exit /b 1
)

echo ✅ Repositorio Git detectado
echo.

:: Verificar que el .exe existe
if not exist "source\dist\MinecraftSSTool.exe" (
    echo ❌ No se encontró source\dist\MinecraftSSTool.exe
    echo.
    echo 💡 Primero debes compilar el proyecto
    echo    Ejecuta: BAT\01-Compilar\COMPILAR_FINAL.bat
    echo.
    pause
    exit /b 1
)

echo ✅ Ejecutable encontrado
echo.

echo 📤 Agregando archivos a Git...
echo.

:: Agregar el .exe
git add -f source/dist/MinecraftSSTool.exe
if %errorlevel% equ 0 (
    echo ✅ source/dist/MinecraftSSTool.exe agregado
) else (
    echo ❌ Error agregando .exe
)

:: Agregar carpetas
git add -f source/build/
git add -f source/build/*
git add -f source/dist/
git add -f source/dist/*

:: Agregar archivos de API para Render
git add -f source/Procfile
git add -f source/gunicorn_config.py
git add -f source/requirements.txt

echo.
echo 📋 Verificando archivos agregados...
echo.
git status --short

echo.
echo ✅ Archivos agregados correctamente
echo.
echo 💡 Próximos pasos:
echo    1. Revisa los archivos listados arriba
echo    2. Si usas GitHub Desktop, verás los cambios ahí
echo    3. Haz commit con: "Agregar ejecutable y archivos para Render"
echo    4. Haz push para subir a GitHub
echo.
echo 📝 O ejecuta estos comandos:
echo    git commit -m "Agregar ejecutable y archivos para Render"
echo    git push
echo.

pause

