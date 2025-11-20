# 🔧 Solución: Error 404 en API

## Problema

La API responde con 404 "Not Found" cuando intentas acceder a `/api/statistics`.

## Causas Posibles

1. **El endpoint no existe** en `api_server.py`
2. **La ruta está mal configurada**
3. **Falta el prefijo `/api` en las rutas**

## Solución Rápida

### Opción 1: Agregar Endpoint de Health Check

Necesitas agregar estos endpoints en `source/api_server.py`:

```python
@app.route('/')
def root():
    """Endpoint raíz para verificar que la API funciona"""
    return jsonify({
        'status': 'ok',
        'service': 'aspers-api',
        'version': '1.0',
        'endpoints': {
            'statistics': '/api/statistics',
            'scans': '/api/scans',
            'health': '/health'
        }
    }), 200

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'aspers-api'}), 200

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Obtiene estadísticas del sistema"""
    # Tu código aquí
    return jsonify({
        'total_scans': 0,
        'total_users': 0,
        # ... más estadísticas
    }), 200
```

### Opción 2: Verificar Rutas Existentes

Si ya tienes endpoints, verifica que tengan el prefijo `/api`:

```python
# ✅ Correcto
@app.route('/api/statistics', methods=['GET'])

# ❌ Incorrecto (sin /api)
@app.route('/statistics', methods=['GET'])
```

## Pasos para Solucionar

### 1. Verificar en GitHub

1. Ve a: `https://github.com/aspersink-svg/aspersprojectsSS`
2. Navega a `source/api_server.py` (o `Aplicación de SS/source/api_server.py`)
3. Busca las rutas definidas con `@app.route`

### 2. Agregar Endpoints Faltantes

Si falta `/api/statistics`, agrégalo en `api_server.py`:

```python
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Obtiene estadísticas"""
    try:
        # Tu lógica aquí
        stats = {
            'total_scans': 0,
            'active_users': 0,
            # ...
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 3. Agregar Endpoint Raíz

Agrega esto al inicio de las rutas en `api_server.py`:

```python
@app.route('/')
def root():
    return jsonify({
        'status': 'ok',
        'service': 'aspers-api',
        'message': 'API is running'
    }), 200
```

### 4. Subir Cambios a GitHub

```bash
git add source/api_server.py
git commit -m "Agregar endpoints de health check y statistics"
git push
```

### 5. Esperar a que Render se Actualice

Render detectará los cambios automáticamente y hará redeploy.

## Verificación

Después de agregar los endpoints:

1. **Prueba:** `https://ssapi-cfni.onrender.com/`
   - Debe responder con JSON

2. **Prueba:** `https://ssapi-cfni.onrender.com/health`
   - Debe responder: `{"status": "ok"}`

3. **Prueba:** `https://ssapi-cfni.onrender.com/api/statistics`
   - Debe responder con estadísticas

## Endpoints Mínimos Necesarios

Tu API debe tener al menos:

- `/` - Endpoint raíz (health check básico)
- `/health` - Health check para Render
- `/api/statistics` - Estadísticas (usado por el panel web)
- `/api/scans` - Lista de escaneos

## Si No Puedes Editar el Código Ahora

**Solución temporal:** Configura el servicio web para que no falle si la API no responde:

En `web_app/app.py`, el código ya maneja errores de conexión, así que el panel web debería funcionar aunque algunos endpoints den 404.


