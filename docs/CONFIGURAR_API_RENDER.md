# 🔧 Configurar API en Render

## Problema

Cuando la aplicación web está en Render, algunos endpoints intentan conectarse a una API externa. Si la API no está configurada correctamente, estos endpoints fallan.

## Solución

Tienes **2 opciones**:

### Opción 1: API en Servicio Separado (Recomendado)

1. **Despliega `source/api_server.py` como un servicio separado en Render:**
   - Tipo: `Web Service`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python api_server.py`
   - Puerto: `5000`

2. **Obtén la URL del servicio de API** (ejemplo: `https://aspers-api.onrender.com`)

3. **En el servicio web (app.py), configura la variable de entorno:**
   ```
   API_URL=https://aspers-api.onrender.com
   ```

### Opción 2: API en el Mismo Servicio

Si quieres que todo funcione en un solo servicio:

1. **Integra los endpoints de la API directamente en `app.py`**
2. **O usa la misma URL base** (ya configurado automáticamente)

## Verificar Configuración

Para verificar que la API está configurada correctamente:

1. Ve a tu servicio en Render
2. En la sección "Environment", verifica:
   - `API_URL` está configurado (si usas servicio separado)
   - `RENDER_EXTERNAL_URL` está automáticamente configurado por Render

## Endpoints que Funcionan Localmente (Sin API Externa)

Estos endpoints ya funcionan sin necesidad de API externa:
- `/api/tokens` (GET, POST, DELETE)
- `/api/auth/*` (login, logout, etc.)
- `/api/admin/*` (gestión de usuarios, empresas)
- `/api/company/*` (gestión de empresa)

## Endpoints que Requieren API Externa

Estos endpoints hacen proxy a la API externa:
- `/api/statistics`
- `/api/scans`
- `/api/feedback`
- `/api/learned-patterns`
- `/api/ai-model/latest`
- `/api/generate-app`
- `/api/get-latest-exe`

## Solución Temporal

Si no puedes desplegar la API externa ahora, puedes:

1. **Comentar temporalmente** los endpoints que requieren API externa
2. **O devolver datos de ejemplo** en lugar de hacer proxy

## Nota Importante

El código actual detecta automáticamente si está en Render usando `RENDER_EXTERNAL_URL`. Si esta variable está configurada, intenta usar la misma URL base para la API. Si necesitas un servicio separado, configura `API_URL`.

