# ✅ Checklist: Verificar Configuración de Render

## Antes de Verificar

1. **¿Reorganizaste el repositorio?** (¿moviste archivos de "Aplicación de SS" a la raíz?)
   - [ ] SÍ → Root Directory debe ser: `source`
   - [ ] NO → Root Directory debe ser: `Aplicación de SS/source`

## Configuración Correcta

### Si reorganizaste (archivos en la raíz):

```
Root Directory: source
Build Command: pip install -r requirements.txt
Start Command: gunicorn api_server:app --config gunicorn_config.py
Runtime: Python 3
Branch: main
```

### Si NO reorganizaste (archivos en "Aplicación de SS"):

```
Root Directory: Aplicación de SS/source
Build Command: pip install -r requirements.txt
Start Command: gunicorn api_server:app --config gunicorn_config.py
Runtime: Python 3
Branch: main
```

## Verificación en GitHub

### Si reorganizaste:
- Ve a: `https://github.com/aspersink-svg/aspersprojectsSS/tree/main/source`
- Debe existir: `Procfile`, `requirements.txt`, `gunicorn_config.py`, `api_server.py`

### Si NO reorganizaste:
- Ve a: `https://github.com/aspersink-svg/aspersprojectsSS/tree/main/Aplicación%20de%20SS/source`
- Debe existir: `Procfile`, `requirements.txt`, `gunicorn_config.py`, `api_server.py`

## Variables de Entorno

En Render → Environment, debe haber:

```
API_SECRET_KEY = [una clave aleatoria]
```

## Qué Hacer Si No Compila

1. **Revisa los Logs** en Render (pestaña "Logs")
2. **Busca errores** específicos
3. **Verifica Root Directory** coincide con la estructura en GitHub
4. **Haz Manual Deploy** → "Deploy latest commit"
5. **Si sigue fallando**, comparte el error específico de los logs

