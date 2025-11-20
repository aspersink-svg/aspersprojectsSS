# 📝 Agregar Endpoints a la API

## Endpoints que Debes Agregar

Copia este código al inicio de las rutas en `source/api_server.py`:

```python
# ============================================================
# HEALTH CHECK Y ENDPOINTS BÁSICOS
# ============================================================

@app.route('/')
def root():
    """Endpoint raíz - verifica que la API funciona"""
    return jsonify({
        'status': 'ok',
        'service': 'aspers-api',
        'version': '1.0',
        'message': 'API is running',
        'endpoints': [
            '/health',
            '/api/statistics',
            '/api/scans'
        ]
    }), 200

@app.route('/health')
@app.route('/healthz')
def health_check():
    """Health check para Render"""
    return jsonify({
        'status': 'ok',
        'service': 'aspers-api',
        'timestamp': datetime.datetime.now().isoformat()
    }), 200

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Obtiene estadísticas del sistema"""
    try:
        # Obtener estadísticas de la base de datos
        with get_db_cursor() as cursor:
            # Total de escaneos
            cursor.execute('SELECT COUNT(*) FROM scans')
            total_scans = cursor.fetchone()[0]
            
            # Escaneos activos
            cursor.execute('SELECT COUNT(*) FROM scans WHERE status = "running"')
            active_scans = cursor.fetchone()[0]
            
            # Total de usuarios
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Total de detecciones
            cursor.execute('SELECT COUNT(*) FROM scan_results WHERE severity = "severe"')
            severe_detections = cursor.fetchone()[0]
        
        return jsonify({
            'total_scans': total_scans,
            'active_scans': active_scans,
            'total_users': total_users,
            'severe_detections': severe_detections,
            'timestamp': datetime.datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
```

## Dónde Agregar el Código

1. **Abre** `source/api_server.py` en GitHub (o localmente)
2. **Busca** donde están definidas las rutas (busca `@app.route`)
3. **Agrega** el código arriba **ANTES** de las otras rutas
4. **Asegúrate** de tener el import de `datetime`:
   ```python
   import datetime
   ```

## Después de Agregar

1. **Sube los cambios a GitHub:**
   ```bash
   git add source/api_server.py
   git commit -m "Agregar endpoints de health check y statistics"
   git push
   ```

2. **Espera 1-2 minutos** a que Render se actualice

3. **Prueba los endpoints:**
   - `https://ssapi-cfni.onrender.com/` → Debe responder JSON
   - `https://ssapi-cfni.onrender.com/health` → Debe responder `{"status": "ok"}`
   - `https://ssapi-cfni.onrender.com/api/statistics` → Debe responder estadísticas


