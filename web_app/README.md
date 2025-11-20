# ASPERS Projects - Panel Web del Staff

Aplicación web moderna para gestión administrativa del sistema ASPERS Security Scanner.

## 🚀 Inicio Rápido

### Instalación

```bash
cd web_app
pip install -r requirements.txt
```

### Configuración

Crear archivo `.env` o establecer variables de entorno:

```bash
export API_URL=http://localhost:5000
export API_KEY=tu-api-key-secreta
export SECRET_KEY=tu-secret-key-flask
```

### Ejecutar

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:8080`

## 📁 Estructura

```
web_app/
├── app.py              # Aplicación Flask principal
├── templates/
│   ├── index.html      # Página principal "Sobre ASPERS"
│   └── panel.html      # Panel del staff
├── static/
│   ├── css/
│   │   ├── style.css   # Estilos principales
│   │   └── panel.css   # Estilos del panel
│   └── js/
│       ├── main.js     # JavaScript principal
│       └── panel.js    # JavaScript del panel
└── requirements.txt
```

## 🔧 Funcionalidades

### 1. Página Principal (index.html)
- Presentación del proyecto ASPERS
- Información sobre funcionalidades
- Diseño moderno y minimalista

### 2. Panel del Staff (panel.html)
- **Dashboard**: Estadísticas y actividad reciente
- **Generar App**: Actualización de la aplicación
- **Tokens**: Gestión de tokens de autenticación
- **Resultados**: Visualización de escaneos

## 🔌 Integración con API

La aplicación web se conecta con la API REST (`source/api_server.py`) para:
- Obtener estadísticas
- Gestionar tokens
- Ver resultados de escaneos
- Generar actualizaciones

## 🎨 Estilo

- Diseño coherente con la aplicación desktop
- Modo oscuro por defecto
- Responsive design
- Animaciones suaves

