# Problemas Pendientes - ASPERS Projects SS

## 🔴 Problema Crítico: Resultados de SS no llegan a la aplicación web

**Fecha:** 21 de Noviembre 2025

**Descripción:**
Los resultados de los escaneos realizados por la aplicación SS (scanner cliente) no están llegando a la aplicación web.

**Posibles causas:**
1. La aplicación SS no está enviando los resultados correctamente a la API
2. La API no está recibiendo/guardando los resultados en la BD
3. La aplicación web no está leyendo los resultados de la BD correctamente
4. Problema de comunicación entre la aplicación SS y la API en Render

**Archivos a revisar:**
- `source/db_integration.py` - Cómo se envían los resultados desde el cliente
- `source/api_server.py` - Endpoint `/api/scans/<id>/results` que recibe los resultados
- `web_app/app.py` - Endpoint `/api/scans` que lista los escaneos
- `source/main.py` - Lógica de envío de resultados desde la aplicación SS

**Pasos para diagnosticar:**
1. Verificar logs de la API cuando se envían resultados
2. Verificar logs de la aplicación SS cuando intenta enviar resultados
3. Verificar que los resultados se guarden en la tabla `scan_results` de la BD
4. Verificar que la aplicación web lea correctamente de `scan_results`

**Notas adicionales:**
- Los tokens ahora se están creando correctamente después de los últimos fixes
- La aplicación SS se conecta a `https://ssapi-cfni.onrender.com`
- La aplicación web está en `https://aspersprojectsss.onrender.com`

---

## 🔴 Problema: Datos de pruebas locales no migrados a Render

**Fecha:** 21 de Noviembre 2025

**Descripción:**
La IA no guardó/migró los datos que tenía cargados de cuando se hizo la prueba en local. Los datos de la base de datos local (escaneos, resultados, patrones aprendidos, feedback del staff, etc.) no están disponibles en Render.

**Datos que probablemente se perdieron:**
- Escaneos realizados en local
- Resultados de escaneos
- Patrones aprendidos (`learned_patterns`)
- Hashes aprendidos (`learned_hashes`)
- Feedback del staff (`staff_feedback`)
- Modelos de IA entrenados
- Estadísticas históricas

**Archivos de BD local:**
- `scanner_db.sqlite` - Base de datos de la API (escaneos, resultados, tokens)
- Posiblemente otros archivos de BD en `web_app/` o `source/`

**Soluciones posibles:**
1. **Exportar datos de BD local e importarlos en Render:**
   - Exportar datos de `scanner_db.sqlite` local
   - Crear script para importar datos en Render (si es posible con SQLite)
   - O migrar a PostgreSQL en Render y luego importar

2. **Usar PostgreSQL en Render (recomendado):**
   - Crear base de datos PostgreSQL en Render
   - Migrar código para usar PostgreSQL en lugar de SQLite
   - Importar datos locales a PostgreSQL
   - Ventaja: Persistencia real, no se pierden datos al reiniciar

3. **Backup periódico:**
   - Implementar sistema de backup automático de la BD
   - Guardar backups en almacenamiento externo (S3, etc.)

**Nota:** En Render tier gratuito, SQLite puede perder datos al reiniciar el servicio. PostgreSQL es más confiable para producción.

