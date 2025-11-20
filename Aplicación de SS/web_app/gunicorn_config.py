"""
Configuración de Gunicorn para Render
"""
import multiprocessing
import os

# Número de workers (procesos)
workers = multiprocessing.cpu_count() * 2 + 1
workers = min(workers, 4)  # Máximo 4 workers en Render free tier

# Timeout (aumentado para evitar 502)
timeout = 180  # 3 minutos
keepalive = 5  # Mantener conexiones vivas

# Bind - Render asigna el puerto automáticamente en la variable PORT
port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker class
worker_class = "sync"

# Preload app (carga la app antes de fork)
preload_app = True

# Max requests (reinicia workers después de N requests para evitar memory leaks)
max_requests = 1000
max_requests_jitter = 50

