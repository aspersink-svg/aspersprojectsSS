# ⚡ Configuración Rápida - PostgreSQL en Render

## ✅ Ya tienes PostgreSQL creado

Tus credenciales:
- **Hostname**: `dpg-d4iuntk9c44c73b5bhfg-a`
- **Port**: `5432`
- **Database**: `aspers_ss_db`
- **User**: `aspers_ss_db_user`
- **Password**: `Dc2Exm9t8oXaBqVZrwcdCV9Ml9tcVhFK`

---

## 🚀 Pasos para Configurar (2 minutos)

### Paso 1: Ir a tu Web App en Render

1. Ve a https://dashboard.render.com
2. Haz clic en tu servicio de **Web App** (el que tiene tu aplicación Flask)

### Paso 2: Agregar Variable de Entorno

1. En tu Web App, ve a la pestaña **"Environment"**
2. Haz clic en **"Add Environment Variable"**
3. Agrega esta variable:

**Nombre:**
```
DATABASE_URL
```

**Valor:**
```
postgresql://aspers_ss_db_user:Dc2Exm9t8oXaBqVZrwcdCV9Ml9tcVhFK@dpg-d4iuntk9c44c73b5bhfg-a:5432/aspers_ss_db
```

4. Haz clic en **"Save Changes"**

### Paso 3: Esperar el Deploy

- Render detectará el cambio automáticamente
- Hará un nuevo deploy (tarda 2-3 minutos)
- Los logs mostrarán: `✅ Usando PostgreSQL`

---

## ✅ ¡Listo!

Una vez que termine el deploy:

1. **Los datos persistirán** después de cada deploy
2. **Los usuarios no se perderán** al actualizar código
3. **Los tokens se mantendrán** entre reinicios

---

## 🔍 Verificar que Funciona

1. Ve a tu aplicación web
2. Crea un usuario nuevo
3. Haz un pequeño cambio en el código y sube a GitHub
4. Render hará un nuevo deploy
5. Verifica que el usuario sigue existiendo ✅

---

## 🆘 Si algo falla

1. Revisa los logs de Render para ver errores
2. Verifica que `DATABASE_URL` esté correcta (sin espacios)
3. Asegúrate de que el servicio PostgreSQL esté activo
4. El código tiene fallback a SQLite, así que no romperá nada

---

## 📝 Nota Importante

**Render PostgreSQL Free**: 
- ✅ 90 días gratis
- ⚠️ Después de 90 días, se pausa automáticamente
- 🔄 Puedes reactivarlo manualmente (gratis) o pagar $7/mes para que esté siempre activo

**Alternativa permanente gratis**: Si necesitas algo que nunca se pause, usa **Supabase** o **Neon** (ver `docs/ALTERNATIVAS_GRATIS_MYSQL.md`)

---

¡Dime cuando lo hayas configurado y te ayudo a verificar que funciona! 🚀

