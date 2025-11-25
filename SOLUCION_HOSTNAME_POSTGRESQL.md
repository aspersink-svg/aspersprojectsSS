# 🔧 Solución: Error "could not translate host name" en PostgreSQL

## ❌ Error
```
could not translate host name "dpg-d4iuntk9c44c73b5bhfg-a" to address: Name or service not known
```

## 🔍 Causa
El hostname en `DATABASE_URL` no tiene el dominio completo. Render necesita el dominio completo para resolver el hostname.

## ✅ Solución

### Paso 1: Obtener el Internal Database URL completo

1. Ve a tu servicio PostgreSQL en Render
2. Ve a la pestaña **"Connections"**
3. Busca **"Internal Database URL"** (NO el "External Database URL")
4. Debe verse así:
   ```
   postgresql://aspers_ss_db_user:Dc2Exm9t8oXaBqVZrwcdCV9Ml9tcVhFK@dpg-d4iuntk9c44c73b5bhfg-a.oregon-postgres.render.com:5432/aspers_ss_db
   ```
   
   **Nota**: Debe incluir `.oregon-postgres.render.com` (o el dominio que corresponda)

### Paso 2: Actualizar DATABASE_URL en tu Web App

1. Ve a tu servicio **Web App** en Render
2. Ve a **"Environment"**
3. Busca la variable `DATABASE_URL`
4. **Reemplázala** con el Internal Database URL completo que copiaste
5. Debe incluir el dominio completo, por ejemplo:
   ```
   postgresql://aspers_ss_db_user:Dc2Exm9t8oXaBqVZrwcdCV9Ml9tcVhFK@dpg-d4iuntk9c44c73b5bhfg-a.oregon-postgres.render.com:5432/aspers_ss_db
   ```
6. Haz clic en **"Save Changes"**

### Paso 3: Reiniciar el servicio

Render debería hacer deploy automáticamente. O haz "Manual Deploy".

## 🔍 Verificar

Después del deploy, en los logs deberías ver:
```
✅ Conexión PostgreSQL establecida
```

En lugar de:
```
❌ Error conectando a PostgreSQL: could not translate host name...
```

## 💡 Nota Importante

- **Internal Database URL**: Para conexiones desde otros servicios de Render (lo que necesitas)
- **External Database URL**: Para conexiones desde fuera de Render (no lo necesitas ahora)

Siempre usa el **Internal Database URL** cuando conectes desde tu Web App a PostgreSQL en Render.

