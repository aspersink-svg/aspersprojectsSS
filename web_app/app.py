"""
Aplicación Web Flask para Panel del Staff de ASPERS Projects
"""
from flask import Flask, render_template, request, jsonify, session, Response, redirect, url_for, make_response
from flask_cors import CORS
import os
import requests
import json
import datetime
import secrets
from functools import wraps

# Importar sistema de autenticación
from auth import (
    init_auth_db, authenticate_user, create_user, create_registration_token,
    verify_registration_token, login_required, admin_required, company_admin_required,
    company_user_required, get_user_by_id, list_registration_tokens, list_users,
    create_company, get_company_by_id, list_companies, update_company,
    has_role, is_admin, is_company_admin, is_company_user
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aspers-secret-key-change-in-production')
CORS(app)

# Inicializar base de datos de autenticación al iniciar (en background para no bloquear)
def init_db_async():
    """Inicializa la BD de forma asíncrona para no bloquear el inicio"""
    try:
        init_auth_db()
        print("✅ Base de datos de autenticación inicializada correctamente")
    except Exception as e:
        print(f"⚠️ Error al inicializar base de datos: {e}")
        print("⚠️ La aplicación continuará, pero algunas funciones pueden no funcionar")

# Inicializar en un thread separado para no bloquear el inicio
import threading
threading.Thread(target=init_db_async, daemon=True).start()

# Health check endpoints (simplificado - sin import externo)

# Configuración
# Detectar si estamos en Render o en desarrollo local
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')  # Render proporciona esta variable
IS_RENDER = bool(RENDER_EXTERNAL_URL)

if IS_RENDER:
    # En Render, verificar si hay una API_URL configurada (servicio separado)
    # Si no, asumir que la API está en el mismo servidor
    api_url_env = os.environ.get('API_URL')
    if api_url_env:
        # API en servicio separado de Render
        API_BASE_URL = api_url_env.rstrip('/')
    else:
        # API en el mismo servidor (mismo servicio)
        base_url = RENDER_EXTERNAL_URL.rstrip('/')
        API_BASE_URL = base_url
else:
    # En desarrollo local, usar localhost:5000
    API_BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')

# IMPORTANTE: La API Key debe coincidir con la que genera api_server.py
# Por defecto, api_server.py genera una aleatoria. Para desarrollo, puedes usar una fija.
API_KEY = os.environ.get('API_KEY', None)  # None = no requiere API key para desarrollo

def get_api_url(endpoint):
    """Construye la URL completa de la API para un endpoint"""
    # Asegurar que el endpoint empiece con /api/
    endpoint = endpoint.lstrip('/')
    if not endpoint.startswith('api/'):
        endpoint = f"api/{endpoint}"
    
    # Si API_URL está configurado explícitamente, usarlo
    api_url_env = os.environ.get('API_URL')
    if api_url_env:
        return f"{api_url_env.rstrip('/')}/{endpoint}"
    
    # Si estamos en Render y no hay API_URL configurado, usar la URL base
    if IS_RENDER:
        return f"{API_BASE_URL}/{endpoint}"
    else:
        # En desarrollo local, usar API_BASE_URL (que es localhost:5000)
        return f"{API_BASE_URL}/{endpoint}"

def require_api_key(f):
    """Decorador para requerir API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # En producción, verificar API key del staff
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Página principal - Sobre ASPERS"""
    response = make_response(render_template('index.html'))
    # Agregar headers de caché para recursos estáticos
    response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutos
    return response

@app.route('/health', methods=['GET'])
@app.route('/healthz', methods=['GET'])
@app.route('/ping', methods=['GET'])
def health_check():
    """Health check endpoint para Render - Optimizado para ser ultra-rápido"""
    # Respuesta mínima y rápida para evitar spinning down
    # Este endpoint se puede llamar periódicamente para mantener el servicio activo
    response = make_response('OK', 200)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/diagnostico-login')
def diagnostico_login():
    """Página de diagnóstico para problemas de login"""
    return render_template('diagnostico_login.html')

@app.route('/api/test-login', methods=['POST'])
def api_test_login():
    """Endpoint de prueba para login"""
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    login_type = data.get('login_type', 'individual')
    
    print(f"API TEST LOGIN - Usuario: '{username}', Tipo: {login_type}")
    
    result = authenticate_user(username, password)
    
    if result['success']:
        user = result['user']
        # Validar tipo de login
        if login_type == 'empresa' and not user.get('company_id'):
            return jsonify({'success': False, 'error': 'Usuario no pertenece a empresa'}), 403
        elif login_type == 'individual' and user.get('company_id'):
            return jsonify({'success': False, 'error': 'Usuario pertenece a empresa'}), 403
        
        return jsonify({'success': True, 'user': user})
    
    return jsonify({'success': False, 'error': result.get('error', 'Error desconocido')}), 401

@app.route('/api/admin/check-user')
def api_check_user():
    """Verifica si un usuario existe"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Username requerido'}), 400
    
    from auth import get_user_by_id
    import sqlite3
    from auth import DATABASE
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, is_active, company_id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'exists': True,
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'is_active': bool(user[3]),
                'company_id': user[4]
            })
        else:
            # Listar usuarios disponibles
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM users LIMIT 10')
            all_users = [u[0] for u in cursor.fetchall()]
            conn.close()
            
            return jsonify({
                'exists': False,
                'available_users': all_users
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        data = request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        login_type = data.get('login_type', 'individual')
        company_name = data.get('company_name', '').strip()
        
        # Validación básica
        if not username or not password:
            error_msg = 'Usuario y contraseña son requeridos'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            return render_template('login.html', error=error_msg)
        
        # Debug logging
        result = authenticate_user(username, password)
        
        if result['success']:
            user = result['user']
            
            # Validación de tipo de login
            if login_type == 'empresa':
                # Si es login empresarial, verificar que el usuario tenga empresa
                if not user.get('company_id'):
                    error_msg = 'Este usuario no pertenece a ninguna empresa. Use el login individual.'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error_msg}), 403
                    return render_template('login.html', error=error_msg)
                
                # Opcional: verificar nombre de empresa si se proporciona
                if company_name:
                    from auth import get_company_by_id
                    company = get_company_by_id(user.get('company_id'))
                    if company and company.get('name', '').lower() != company_name.lower():
                        error_msg = f'El nombre de empresa no coincide. Empresa del usuario: {company.get("name", "N/A")}'
                        if request.is_json:
                            return jsonify({'success': False, 'error': error_msg}), 403
                        return render_template('login.html', error=error_msg)
            
            elif login_type == 'individual':
                # Si es login individual, verificar que NO tenga empresa
                if user.get('company_id'):
                    error_msg = 'Este usuario pertenece a una empresa. Use el login empresarial.'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error_msg}), 403
                    return render_template('login.html', error=error_msg)
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['roles'] = user['roles']  # Múltiples roles
            session['company_id'] = user.get('company_id')
            
            if request.is_json:
                return jsonify({'success': True, 'user': user})
            
            return redirect(url_for('panel'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': result['error']}), 401
            
            return render_template('login.html', error=result['error'])
    
    # Si ya está logueado, redirigir al panel
    if 'user_id' in session:
        return redirect(url_for('panel'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro con token"""
    if request.method == 'POST':
        data = request.form
        token = data.get('token', '')
        username = data.get('username', '')
        password = data.get('password', '')
        email = data.get('email', '')
        
        # Verificar token
        token_result = verify_registration_token(token)
        if not token_result['success']:
            if request.is_json:
                return jsonify({'success': False, 'error': token_result['error']}), 400
            return render_template('register.html', error=token_result['error'])
        
        # Determinar roles según el tipo de token
        company_id = token_result.get('company_id')
        is_admin_token = token_result.get('is_admin_token', False)
        
        # Debug: Verificar valores del token
        print(f"  company_id: {company_id}")
        print(f"  is_admin_token (raw): {is_admin_token}")
        print(f"  is_admin_token (type): {type(is_admin_token)}")
        print(f"  is_admin_token (bool): {bool(is_admin_token)}")
        
        # Asegurar que is_admin_token sea un booleano
        if isinstance(is_admin_token, int):
            is_admin_token = bool(is_admin_token)
        elif isinstance(is_admin_token, str):
            is_admin_token = is_admin_token.lower() in ('true', '1', 'yes')
        
        if company_id:
            # Usuario de empresa
            if is_admin_token:
                roles = ['empresa', 'administrador']
            else:
                roles = ['empresa', 'staff']
        else:
            # Usuario normal (sin empresa)
            roles = ['user']
        
        # Crear usuario
        user_result = create_user(
            username=username,
            password=password,
            email=email if email else None,
            roles=roles,
            company_id=company_id,
            created_by=token_result['created_by']
        )
        
        if user_result['success']:
            if request.is_json:
                return jsonify({'success': True, 'message': 'Usuario creado exitosamente'})
            
            return render_template('register.html', success=True)
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': user_result['error']}), 400
            
            return render_template('register.html', error=user_result['error'])
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/panel')
@login_required
def panel():
    """Panel del staff - Requiere autenticación"""
    user = get_user_by_id(session.get('user_id'))
    # Asegurar que user tiene roles como lista para el template
    if user and isinstance(user.get('roles'), str):
        import json
        try:
            user['roles'] = json.loads(user['roles'])
        except:
            user['roles'] = [user.get('roles', 'user')]
    return render_template('panel.html', user=user)

@app.route('/admin/subscriptions', methods=['GET', 'POST'])
def admin_subscriptions():
    """Página secreta de administrador para gestionar suscripciones"""
    # Autenticación especial para esta página
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Verificar credenciales de admin (puedes cambiar esto)
        if username == 'admin' and password == 'admin123':  # ⚠️ CAMBIAR EN PRODUCCIÓN
            session['admin_subscriptions'] = True
            return redirect('/admin/subscriptions')
        else:
            return render_template('admin_subscriptions_login.html', error='Credenciales incorrectas')
    
    # Verificar si está autenticado
    if not session.get('admin_subscriptions'):
        return render_template('admin_subscriptions_login.html')
    
    # Si está autenticado, mostrar panel de gestión
    from auth import list_companies, list_users, create_company, update_company
    
    companies = list_companies()
    users = list_users()
    
    # Separar usuarios individuales (sin empresa) y usuarios de empresa
    individual_users = [u for u in users if not u.get('company_id')]
    company_users = [u for u in users if u.get('company_id')]
    
    return render_template('admin_subscriptions.html', 
                         companies=companies, 
                         individual_users=individual_users,
                         company_users=company_users)

@app.route('/admin/subscriptions/logout')
def admin_subscriptions_logout():
    """Cerrar sesión de admin de suscripciones"""
    session.pop('admin_subscriptions', None)
    return redirect('/admin/subscriptions')

# ============================================================
# API PROXY - Conecta con la API REST
# ============================================================

# ============================================================
# FUNCIONES DE BASE DE DATOS COMPARTIDAS (SIN LATENCIA DE RED)
# ============================================================
import sqlite3
from contextlib import contextmanager

# Usar la misma base de datos que la API
API_DATABASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'source', 'scanner_db.sqlite')

@contextmanager
def get_api_db_cursor():
    """Context manager para operaciones de base de datos de la API - SIN HTTP"""
    conn = sqlite3.connect(API_DATABASE, check_same_thread=False, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Caché simple en memoria para estadísticas
_stats_cache = {}
_stats_cache_time = {}

@app.route('/api/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Obtiene estadísticas - OPTIMIZADO: Acceso directo a BD sin HTTP"""
    import time
    
    # Verificar caché (30 segundos TTL)
    cache_key = 'statistics'
    if cache_key in _stats_cache:
        if time.time() - _stats_cache_time.get(cache_key, 0) < 30:
            return jsonify(_stats_cache[cache_key]), 200
    
    try:
        # Acceso directo a la base de datos (SIN HTTP - MUCHO MÁS RÁPIDO)
        with get_api_db_cursor() as cursor:
            stats = {
                'total_scans': 0,
                'active_scans': 0,
                'unique_machines': 0,
                'severe_detections': 0,
                'total_results': 0,
                'active_tokens': 0,
                'total_bans': 0
            }
            
            # Consulta optimizada: una sola query
            try:
                cursor.execute('''
                    SELECT 
                        (SELECT COUNT(*) FROM scans) as total_scans,
                        (SELECT COUNT(*) FROM scans WHERE status = "running") as active_scans,
                        (SELECT COUNT(DISTINCT machine_id) FROM scans WHERE machine_id IS NOT NULL AND machine_id != "") as unique_machines,
                        (SELECT COUNT(*) FROM scan_results WHERE alert_level = "CRITICAL") as severe_detections,
                        (SELECT COUNT(*) FROM scan_results) as total_results,
                        (SELECT COUNT(*) FROM scan_tokens WHERE is_active = 1) as active_tokens,
                        (SELECT COUNT(*) FROM ban_history) as total_bans
                ''')
                row = cursor.fetchone()
                if row:
                    stats['total_scans'] = row[0] or 0
                    stats['active_scans'] = row[1] or 0
                    stats['unique_machines'] = row[2] or 0
                    stats['severe_detections'] = row[3] or 0
                    stats['total_results'] = row[4] or 0
                    stats['active_tokens'] = row[5] or 0
                    stats['total_bans'] = row[6] or 0
            except sqlite3.OperationalError:
                # Fallback: consultas individuales si alguna tabla no existe
                for query, key in [
                    ('SELECT COUNT(*) FROM scans', 'total_scans'),
                    ('SELECT COUNT(*) FROM scans WHERE status = "running"', 'active_scans'),
                    ('SELECT COUNT(DISTINCT machine_id) FROM scans WHERE machine_id IS NOT NULL AND machine_id != ""', 'unique_machines'),
                    ('SELECT COUNT(*) FROM scan_results WHERE alert_level = "CRITICAL"', 'severe_detections'),
                    ('SELECT COUNT(*) FROM scan_results', 'total_results'),
                    ('SELECT COUNT(*) FROM scan_tokens WHERE is_active = 1', 'active_tokens'),
                    ('SELECT COUNT(*) FROM ban_history', 'total_bans')
                ]:
                    try:
                        cursor.execute(query)
                        stats[key] = cursor.fetchone()[0] or 0
                    except sqlite3.OperationalError:
                        pass
            
            stats['timestamp'] = datetime.datetime.now().isoformat()
            
            # Guardar en caché
            _stats_cache[cache_key] = stats
            _stats_cache_time[cache_key] = time.time()
            
            return jsonify(stats), 200
    except Exception as e:
        import traceback
        print(f"Error en get_statistics: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

# ============================================================
# API DE AUTENTICACIÓN
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint para login"""
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    result = authenticate_user(username, password)
    
    if result['success']:
        session['user_id'] = result['user']['id']
        session['username'] = result['user']['username']
        session['roles'] = result['user']['roles']
        session['company_id'] = result['user'].get('company_id')
        return jsonify({'success': True, 'user': result['user']})
    else:
        return jsonify({'success': False, 'error': result['error']}), 401

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint para logout"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
@login_required
def api_me():
    """Obtiene información del usuario actual"""
    user = get_user_by_id(session.get('user_id'))
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """API endpoint para registro"""
    data = request.json or {}
    token = data.get('token', '')
    username = data.get('username', '')
    password = data.get('password', '')
    email = data.get('email', '')
    
    # Verificar token
    token_result = verify_registration_token(token)
    if not token_result['success']:
        return jsonify({'success': False, 'error': token_result['error']}), 400
    
    # Determinar roles según el tipo de token
    company_id = token_result.get('company_id')
    is_admin_token = token_result.get('is_admin_token', False)
    
    if company_id:
        # Usuario de empresa
        if is_admin_token:
            roles = ['empresa', 'administrador']
        else:
            roles = ['empresa', 'staff']
    else:
        # Usuario normal (sin empresa)
        roles = ['user']
    
    # Crear usuario
    user_result = create_user(
        username=username,
        password=password,
        email=email if email else None,
        roles=roles,
        company_id=company_id,
        created_by=token_result['created_by']
    )
    
    if user_result['success']:
        return jsonify({'success': True, 'message': 'Usuario creado exitosamente'})
    else:
        return jsonify({'success': False, 'error': user_result['error']}), 400

# ============================================================
# API DE ADMINISTRACIÓN (Solo para admins)
# ============================================================

@app.route('/api/admin/registration-tokens', methods=['GET'])
@admin_required
def api_list_registration_tokens():
    """Lista tokens de registro (solo admin)"""
    include_used = request.args.get('include_used', 'false').lower() == 'true'
    tokens = list_registration_tokens(include_used=include_used)
    return jsonify({'success': True, 'tokens': tokens})

@app.route('/api/admin/registration-tokens', methods=['POST'])
@admin_required
def api_create_registration_token():
    """Crea un token de registro (solo admin) - Puede ser para empresa o general"""
    data = request.json or {}
    expires_hours = data.get('expires_hours', 24)
    description = data.get('description', '')
    company_id = data.get('company_id')  # Opcional: si se proporciona, es token de empresa
    is_admin_token = data.get('is_admin_token', False)  # Si es True, crea admin de empresa
    
    created_by = session.get('user_id')
    if not created_by:
        return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401
    
    result = create_registration_token(
        created_by=created_by,
        company_id=company_id,
        expires_hours=expires_hours,
        description=description,
        is_admin_token=is_admin_token
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'token': result['token'],
            'token_id': result['token_id'],
            'expires_at': result['expires_at'].isoformat(),
            'company_id': company_id,
            'is_admin_token': is_admin_token
        }), 201
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def api_list_users():
    """Lista usuarios (solo admin) - Puede filtrar por empresa"""
    company_id = request.args.get('company_id', type=int)
    users = list_users(company_id=company_id)
    return jsonify({'success': True, 'users': users})

# ============================================================
# API DE GESTIÓN DE EMPRESAS
# ============================================================

@app.route('/api/admin/companies', methods=['GET'])
@admin_required
def api_list_companies():
    """Lista todas las empresas (solo super admin)"""
    companies = list_companies()
    return jsonify({'success': True, 'companies': companies})

@app.route('/api/admin/companies', methods=['POST'])
@admin_required
def api_create_company():
    """Crea una nueva empresa (solo super admin)"""
    data = request.json or {}
    
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'error': 'El nombre de la empresa es requerido'}), 400
    
    result = create_company(
        name=name,
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone'),
        max_users=data.get('max_users', 8),
        max_admins=data.get('max_admins', 3),
        created_by=session.get('user_id'),
        notes=data.get('notes')
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'company_id': result['company_id']
        }), 201
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

@app.route('/api/admin/companies/<int:company_id>', methods=['GET'])
@admin_required
def api_get_company(company_id):
    """Obtiene información de una empresa"""
    company = get_company_by_id(company_id)
    if company:
        return jsonify({'success': True, 'company': company})
    return jsonify({'success': False, 'error': 'Empresa no encontrada'}), 404

@app.route('/api/admin/companies/<int:company_id>', methods=['PUT'])
@admin_required
def api_update_company(company_id):
    """Actualiza una empresa"""
    data = request.json or {}
    
    result = update_company(
        company_id=company_id,
        name=data.get('name'),
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone'),
        subscription_status=data.get('subscription_status'),
        subscription_end_date=data.get('subscription_end_date'),
        max_users=data.get('max_users'),
        max_admins=data.get('max_admins'),
        is_active=data.get('is_active'),
        notes=data.get('notes')
    )
    
    if result['success']:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

@app.route('/api/company/registration-tokens', methods=['GET'])
@company_admin_required
def api_list_company_tokens():
    """Lista tokens de registro de la empresa del usuario (admin de empresa)"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    include_used = request.args.get('include_used', 'false').lower() == 'true'
    tokens = list_registration_tokens(include_used=include_used, company_id=user['company_id'])
    return jsonify({'success': True, 'tokens': tokens})

@app.route('/api/company/registration-tokens', methods=['POST'])
@company_admin_required
def api_create_company_token():
    """Crea un token de registro para la empresa (admin de empresa)"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    data = request.json or {}
    expires_hours = data.get('expires_hours', 24)
    description = data.get('description', '')
    is_admin_token = data.get('is_admin_token', False)
    
    # Asegurar que is_admin_token sea un booleano
    if isinstance(is_admin_token, str):
        is_admin_token = is_admin_token.lower() in ('true', '1', 'yes')
    elif not isinstance(is_admin_token, bool):
        is_admin_token = bool(is_admin_token)
    
    result = create_registration_token(
        created_by=session.get('user_id'),
        company_id=user['company_id'],
        expires_hours=expires_hours,
        description=description,
        is_admin_token=is_admin_token
    )
    
    if result['success']:
        return jsonify({
            'success': True,
            'token': result['token'],
            'token_id': result['token_id'],
            'expires_at': result['expires_at'].isoformat(),
            'is_admin_token': is_admin_token
        }), 201
    else:
        return jsonify({'success': False, 'error': result['error']}), 400

@app.route('/api/company/users', methods=['GET'])
@company_admin_required
def api_list_company_users():
    """Lista usuarios de la empresa (admin de empresa)"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    users = list_users(company_id=user['company_id'])
    return jsonify({'success': True, 'users': users})

@app.route('/api/company/users/<int:user_id>/deactivate', methods=['POST'])
@company_admin_required
def api_deactivate_company_user(user_id):
    """Desactiva un usuario de la empresa (admin de empresa)"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    # Verificar que el usuario a desactivar pertenece a la misma empresa
    target_user = get_user_by_id(user_id)
    if not target_user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    
    if target_user.get('company_id') != user['company_id']:
        return jsonify({'success': False, 'error': 'No tienes permiso para modificar este usuario'}), 403
    
    # No permitir desactivarse a sí mismo
    if user_id == user['id']:
        return jsonify({'success': False, 'error': 'No puedes desactivar tu propia cuenta'}), 400
    
    try:
        import sqlite3
        from auth import DATABASE
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Usuario desactivado exitosamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/company/users/<int:user_id>/activate', methods=['POST'])
@company_admin_required
def api_activate_company_user(user_id):
    """Activa un usuario de la empresa (admin de empresa)"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    # Verificar que el usuario a activar pertenece a la misma empresa
    target_user = get_user_by_id(user_id)
    if not target_user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    
    if target_user.get('company_id') != user['company_id']:
        return jsonify({'success': False, 'error': 'No tienes permiso para modificar este usuario'}), 403
    
    try:
        import sqlite3
        from auth import DATABASE
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Usuario activado exitosamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/company/users/<int:user_id>/delete', methods=['DELETE'])
@company_admin_required
def api_delete_company_user(user_id):
    """Elimina un usuario de la empresa (admin de empresa)"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    # Verificar que el usuario a eliminar pertenece a la misma empresa
    target_user = get_user_by_id(user_id)
    if not target_user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    
    if target_user.get('company_id') != user['company_id']:
        return jsonify({'success': False, 'error': 'No tienes permiso para eliminar este usuario'}), 403
    
    # No permitir eliminarse a sí mismo
    if user_id == user['id']:
        return jsonify({'success': False, 'error': 'No puedes eliminar tu propia cuenta'}), 400
    
    try:
        import sqlite3
        from auth import DATABASE
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Usuario eliminado exitosamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/company/info', methods=['GET'])
@company_user_required
def api_get_company_info():
    """Obtiene información de la empresa del usuario"""
    user = get_user_by_id(session.get('user_id'))
    if not user or not user.get('company_id'):
        return jsonify({'success': False, 'error': 'Usuario no pertenece a una empresa'}), 403
    
    company = get_company_by_id(user['company_id'])
    if company:
        return jsonify({'success': True, 'company': company})
    return jsonify({'success': False, 'error': 'Empresa no encontrada'}), 404

# ============================================================
# API DE ADMINISTRACIÓN DE SUSCRIPCIONES (Página Secreta)
# ============================================================

def admin_subscriptions_required(f):
    """Decorador para requerir autenticación de admin de suscripciones"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_subscriptions'):
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/create-subscription', methods=['POST'])
@admin_subscriptions_required
def api_create_subscription():
    """Crea una nueva suscripción (individual o empresarial)"""
    data = request.json or {}
    
    subscription_type = data.get('subscription_type', 'individual')
    price = data.get('price', 5.0 if subscription_type == 'individual' else 13.0)
    duration = data.get('duration', 1)  # meses
    is_free = data.get('is_free', False)
    
    if is_free:
        price = 0.0
    
    try:
        if subscription_type == 'enterprise':
            # Crear empresa
            company_name = data.get('company_name')
            if not company_name:
                return jsonify({'success': False, 'error': 'Nombre de empresa requerido'}), 400
            
            result = create_company(
                name=company_name,
                contact_email=data.get('email'),
                subscription_type='enterprise',
                subscription_status='active',
                subscription_price=price,
                max_users=8,
                max_admins=3,
                created_by=None,
                notes=f'Suscripción creada desde panel admin. Duración: {duration} meses'
            )
            
            if result['success']:
                # Calcular fecha de expiración
                if duration > 0:
                    from datetime import datetime, timedelta
                    end_date = datetime.now() + timedelta(days=duration * 30)
                    update_company(
                        company_id=result['company_id'],
                        subscription_end_date=end_date.isoformat()
                    )
                
                return jsonify({
                    'success': True,
                    'company_id': result['company_id'],
                    'message': 'Suscripción empresarial creada'
                })
            else:
                return jsonify({'success': False, 'error': result['error']}), 400
        
        else:  # individual
            # Crear usuario individual
            username = data.get('username')
            email = data.get('email')
            
            if not username:
                return jsonify({'success': False, 'error': 'Nombre de usuario requerido'}), 400
            
            # Generar contraseña temporal
            import secrets
            temp_password = secrets.token_urlsafe(12)
            
            result = create_user(
                username=username,
                password=temp_password,
                email=email,
                roles=['user'],
                company_id=None,
                created_by='admin_subscriptions'
            )
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'user_id': result['user_id'],
                    'temp_password': temp_password,
                    'message': f'Suscripción individual creada. Contraseña temporal: {temp_password}'
                })
            else:
                return jsonify({'success': False, 'error': result['error']}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/make-free', methods=['POST'])
@admin_subscriptions_required
def api_make_free():
    """Marca una suscripción como gratuita"""
    data = request.json or {}
    sub_id = data.get('id')
    sub_type = data.get('type')  # 'company' o 'user'
    
    try:
        if sub_type == 'company':
            result = update_company(
                company_id=sub_id,
                subscription_price=0.0,
                subscription_status='active'
            )
            if result['success']:
                return jsonify({'success': True, 'message': 'Empresa marcada como gratuita'})
        else:  # user
            # Para usuarios individuales, podríamos crear una "empresa" especial o solo marcarlos
            # Por ahora, solo confirmamos
            return jsonify({'success': True, 'message': 'Usuario individual marcado como gratuito'})
        
        return jsonify({'success': False, 'error': 'Error al actualizar'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/update-company', methods=['POST'])
@admin_subscriptions_required
def api_admin_update_company():
    """Actualiza una empresa desde el panel de administración secreto"""
    data = request.json or {}
    company_id = data.get('company_id')
    
    if not company_id:
        return jsonify({'success': False, 'error': 'ID de empresa requerido'}), 400
    
    try:
        result = update_company(
            company_id=company_id,
            name=data.get('name'),
            contact_email=data.get('contact_email'),
            subscription_price=data.get('subscription_price'),
            max_users=data.get('max_users'),
            max_admins=data.get('max_admins'),
            subscription_status=data.get('subscription_status'),
            subscription_end_date=data.get('subscription_end_date')
        )
        
        if result['success']:
            return jsonify({'success': True, 'message': 'Empresa actualizada exitosamente'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Error desconocido')}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# API PROXY - Conecta con la API REST
# ============================================================

# IMPORTANTE: Separación de tokens
# - /api/tokens -> Tokens de ESCANEO (para la aplicación SS) - Tabla: scan_tokens
# - /api/registration-tokens -> Tokens de REGISTRO (para usuarios) - Tabla: registration_tokens

@app.route('/api/tokens', methods=['GET'])
@admin_required
def list_tokens():
    """Lista tokens de ESCANEO (para la aplicación SS) - CORREGIDO"""
    try:
        # Listar tokens de ESCANEO desde la BD de la API (scan_tokens)
        with get_api_db_cursor() as cursor:
            cursor.execute('''
                SELECT id, token, created_at, expires_at, used_count, max_uses, 
                       is_active, created_by, description
                FROM scan_tokens
                ORDER BY created_at DESC
                LIMIT 100
            ''')
            
            tokens = []
            for row in cursor.fetchall():
                tokens.append({
                    'id': row[0],
                    'token': row[1],
                    'created_at': row[2],
                    'expires_at': row[3],
                    'used_count': row[4],
                    'max_uses': row[5],
                    'is_active': bool(row[6]),
                    'created_by': row[7],
                    'description': row[8],
                    'type': 'scan_token'  # Indicar que es un token de escaneo
                })
        
        return jsonify({'success': True, 'tokens': tokens})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tokens', methods=['POST'])
@admin_required
def create_token():
    """Crea un nuevo token de ESCANEO (para la aplicación SS) - CORREGIDO"""
    import secrets
    try:
        data = request.json or {}
        
        # Convertir días a horas si viene en días
        expires_days = data.get('expires_days', data.get('expires_hours', 1) / 24 if 'expires_hours' in data else 30)
        if 'expires_hours' in data:
            expires_days = data.get('expires_hours', 24) / 24
        
        max_uses = data.get('max_uses', -1)  # -1 = ilimitado
        description = data.get('description', '')
        
        # Obtener usuario actual
        user = get_user_by_id(session.get('user_id'))
        created_by = user.get('username', 'web_app') if user else 'web_app'
        
        # Crear token de ESCANEO directamente en la BD de la API (scan_tokens)
        # NOTA: Este es un token de ESCANEO, no de registro de usuarios
        token = secrets.token_urlsafe(32)
        expires_at = None
        if expires_days > 0:
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=expires_days)).isoformat()
        
        # Insertar directamente en scan_tokens (tabla de la API)
        with get_api_db_cursor() as cursor:
            cursor.execute('''
                INSERT INTO scan_tokens (token, expires_at, max_uses, description, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (token, expires_at, max_uses, description, created_by))
            
            token_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'token': token,
            'token_id': token_id,
            'expires_at': expires_at,
            'max_uses': max_uses,
            'description': description,
            'type': 'scan_token'  # Indicar que es un token de escaneo
        }), 201
    except Exception as e:
        import traceback
        error_msg = f'Error inesperado al crear token de escaneo: {str(e)}'
        print(f"ERROR create_token: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/tokens/<int:token_id>', methods=['DELETE'])
@admin_required
def delete_token(token_id):
    """Elimina permanentemente un token de ESCANEO - CORREGIDO"""
    try:
        # Eliminar token de ESCANEO desde la BD de la API (scan_tokens)
        with get_api_db_cursor() as cursor:
            # Verificar que el token existe
            cursor.execute('SELECT id FROM scan_tokens WHERE id = ?', (token_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Token no encontrado'}), 404
            
            cursor.execute('DELETE FROM scan_tokens WHERE id = ?', (token_id,))
        
        return jsonify({'success': True, 'message': 'Token de escaneo eliminado exitosamente'}), 200
    except Exception as e:
        import traceback
        print(f"Error al eliminar token: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Error al eliminar token: {str(e)}'}), 500

@app.route('/api/scans', methods=['GET'])
@login_required
def list_scans():
    """Lista escaneos - OPTIMIZADO: Acceso directo a BD sin HTTP"""
    import time
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Caché por limit/offset (10 segundos TTL)
    cache_key = f'scans_list_{limit}_{offset}'
    if cache_key in _stats_cache:
        if time.time() - _stats_cache_time.get(cache_key, 0) < 10:
            return jsonify(_stats_cache[cache_key]), 200
    
    try:
        # Acceso directo a BD (SIN HTTP - MUCHO MÁS RÁPIDO)
        with get_api_db_cursor() as cursor:
            cursor.execute('''
                SELECT id, scan_token, started_at, completed_at, status,
                       total_files_scanned, issues_found, scan_duration, machine_name
                FROM scans
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            scans = []
            scan_ids = []
            for row in cursor.fetchall():
                scan_id = row[0]
                scan_ids.append(scan_id)
                scans.append({
                    'id': scan_id,
                    'scan_token': row[1],
                    'started_at': row[2],
                    'completed_at': row[3],
                    'status': row[4],
                    'total_files_scanned': row[5],
                    'issues_found': row[6],
                    'scan_duration': row[7],
                    'machine_name': row[8]
                })
            
            # Calcular preview de severidad (una sola query optimizada)
            if scan_ids:
                placeholders = ','.join(['?'] * len(scan_ids))
                cursor.execute(f'''
                    SELECT scan_id, 
                           SUM(CASE WHEN alert_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
                           SUM(CASE WHEN alert_level IN ('SOSPECHOSO', 'HACKS') THEN 1 ELSE 0 END) as suspicious,
                           SUM(CASE WHEN alert_level = 'POCO_SOSPECHOSO' THEN 1 ELSE 0 END) as low,
                           COUNT(*) as total
                    FROM scan_results
                    WHERE scan_id IN ({placeholders})
                    GROUP BY scan_id
                ''', scan_ids)
                
                severity_map = {}
                for row in cursor.fetchall():
                    scan_id, critical, suspicious, low, total = row
                    if critical > 0:
                        severity_map[scan_id] = {'summary': 'CRITICO', 'badge': 'danger'}
                    elif suspicious > 0:
                        severity_map[scan_id] = {'summary': 'SOSPECHOSO', 'badge': 'warning'}
                    elif low > 0:
                        severity_map[scan_id] = {'summary': 'POCO_SOSPECHOSO', 'badge': 'info'}
                    elif total == 0:
                        severity_map[scan_id] = {'summary': 'LIMPIO', 'badge': 'success'}
                    else:
                        severity_map[scan_id] = {'summary': 'NORMAL', 'badge': 'secondary'}
                
                # Agregar preview a cada scan
                for scan in scans:
                    if scan['id'] in severity_map:
                        scan['severity_summary'] = severity_map[scan['id']]['summary']
                        scan['severity_badge'] = severity_map[scan['id']]['badge']
                    else:
                        scan['severity_summary'] = 'LIMPIO' if scan['issues_found'] == 0 else 'SOSPECHOSO'
                        scan['severity_badge'] = 'success' if scan['issues_found'] == 0 else 'warning'
            
            result = {'scans': scans}
            
            # Guardar en caché
            _stats_cache[cache_key] = result
            _stats_cache_time[cache_key] = time.time()
            
            return jsonify(result), 200
    except Exception as e:
        import traceback
        print(f"Error en list_scans: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

@app.route('/api/scans/<int:scan_id>', methods=['GET'])
@login_required
def get_scan(scan_id):
    """Obtiene un escaneo específico - OPTIMIZADO: Acceso directo a BD sin HTTP"""
    import time
    
    # Caché por scan_id (5 segundos TTL)
    cache_key = f'scan_{scan_id}'
    if cache_key in _stats_cache:
        if time.time() - _stats_cache_time.get(cache_key, 0) < 5:
            return jsonify(_stats_cache[cache_key]), 200
    
    try:
        # Acceso directo a BD (SIN HTTP - MUCHO MÁS RÁPIDO)
        with get_api_db_cursor() as cursor:
            cursor.execute('''
                SELECT id, token_id, scan_token, started_at, completed_at, status,
                       total_files_scanned, issues_found, scan_duration, machine_id, machine_name,
                       ip_address, country, minecraft_username
                FROM scans
                WHERE id = ?
            ''', (scan_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Escaneo no encontrado'}), 404
            
            scan = {
                'id': row[0],
                'token_id': row[1],
                'scan_token': row[2],
                'started_at': row[3],
                'completed_at': row[4],
                'status': row[5],
                'total_files_scanned': row[6],
                'issues_found': row[7],
                'scan_duration': row[8],
                'machine_id': row[9],
                'machine_name': row[10],
                'ip_address': row[11] if len(row) > 11 else None,
                'country': row[12] if len(row) > 12 else None,
                'minecraft_username': row[13] if len(row) > 13 else None
            }
            
            # Obtener resultados
            cursor.execute('''
                SELECT id, issue_type, issue_name, issue_path, issue_category,
                       alert_level, confidence, detected_patterns, obfuscation_detected,
                       file_hash, ai_analysis, ai_confidence
                FROM scan_results
                WHERE scan_id = ?
            ''', (scan_id,))
            
            results = []
            for r in cursor.fetchall():
                results.append({
                    'id': r[0],
                    'issue_type': r[1],
                    'issue_name': r[2],
                    'issue_path': r[3],
                    'issue_category': r[4],
                    'alert_level': r[5],
                    'confidence': r[6],
                    'detected_patterns': json.loads(r[7]) if r[7] else [],
                    'obfuscation_detected': bool(r[8]),
                    'file_hash': r[9],
                    'ai_analysis': r[10],
                    'ai_confidence': r[11]
                })
            
            scan['results'] = results
            
            # Guardar en caché
            _stats_cache[cache_key] = scan
            _stats_cache_time[cache_key] = time.time()
            
            return jsonify(scan), 200
    except Exception as e:
        import traceback
        print(f"Error en get_scan: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Envía feedback del staff sobre un resultado"""
    try:
        data = request.json or {}
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Validar que tenga los campos requeridos
        if 'result_id' not in data:
            return jsonify({'error': 'Se requiere result_id'}), 400
        
        headers = {}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        
        # Intentar conectar a la API
        try:
            response = requests.post(
                get_api_url('/api/feedback'),
                json=data,
                headers=headers,
                timeout=5  # Reducido de 10 a 5 segundos
            )
        except requests.exceptions.ConnectionError:
            error_msg = 'No se pudo conectar a la API.'
            if IS_RENDER:
                error_msg += ' En Render, asegúrate de que la API esté configurada correctamente.'
            else:
                error_msg += ' Verifica que esté corriendo en http://localhost:5000'
            return jsonify({'error': error_msg}), 503
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Timeout al conectar con la API'}), 504
        except Exception as e:
            return jsonify({'error': f'Error de conexión: {str(e)}'}), 500
        
        # Procesar respuesta
        if response.status_code == 201:
            return jsonify(response.json()), 201
        elif response.status_code == 400:
            # Intentar obtener mensaje de error más detallado
            try:
                error_data = response.json()
                return jsonify({'error': error_data.get('error', 'Error al enviar feedback')}), 400
            except:
                return jsonify({'error': f'Error al enviar feedback: {response.text}'}), 400
        else:
            # Otros códigos de error
            try:
                error_data = response.json()
                return jsonify({'error': error_data.get('error', f'Error {response.status_code}')}), response.status_code
            except:
                return jsonify({'error': f'Error al enviar feedback: {response.status_code} - {response.text}'}), response.status_code
    except Exception as e:
        import traceback
        return jsonify({'error': f'Error inesperado: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/feedback/batch', methods=['POST'])
@login_required
def submit_feedback_batch():
    """Envía feedback masivo del staff sobre múltiples resultados"""
    try:
        data = request.json or {}
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Validar que tenga los campos requeridos
        if 'result_ids' not in data or not isinstance(data.get('result_ids'), list):
            return jsonify({'error': 'Se requiere result_ids como lista'}), 400
        
        if len(data.get('result_ids', [])) == 0:
            return jsonify({'error': 'La lista de result_ids está vacía'}), 400
        
        headers = {}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        
        # Intentar conectar a la API
        try:
            response = requests.post(
                get_api_url('/api/feedback/batch'),
                json=data,
                headers=headers,
                timeout=30
            )
        except requests.exceptions.ConnectionError:
            error_msg = 'No se pudo conectar a la API.'
            if IS_RENDER:
                error_msg += ' En Render, asegúrate de que la API esté configurada correctamente.'
            else:
                error_msg += ' Verifica que esté corriendo en http://localhost:5000'
            return jsonify({'error': error_msg}), 503
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Timeout al conectar con la API'}), 504
        except Exception as e:
            return jsonify({'error': f'Error de conexión: {str(e)}'}), 500
        
        # Procesar respuesta
        if response.status_code == 201:
            return jsonify(response.json()), 201
        elif response.status_code == 404:
            return jsonify({
                'error': f'Endpoint no encontrado en la API. Verifica que la API esté corriendo y tenga el endpoint /api/feedback/batch. Status: {response.status_code}',
                'details': response.text[:200]
            }), 404
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return jsonify({'error': error_data.get('error', 'Error al enviar feedback masivo')}), 400
            except:
                return jsonify({'error': f'Error al enviar feedback masivo: {response.text}'}), 400
        else:
            try:
                error_data = response.json()
                return jsonify({
                    'error': error_data.get('error', f'Error {response.status_code}'),
                    'status_code': response.status_code,
                    'response_text': response.text[:200]
                }), response.status_code
            except:
                return jsonify({
                    'error': f'Error al enviar feedback masivo: {response.status_code}',
                    'response_text': response.text[:200]
                }), response.status_code
    except Exception as e:
        import traceback
        return jsonify({'error': f'Error inesperado: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/feedback/<int:result_id>', methods=['GET'])
def get_feedback(result_id):
    """Obtiene feedback de un resultado específico"""
    try:
        headers = {}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        response = requests.get(
            get_api_url(f'/api/feedback/{result_id}'),
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Error al obtener feedback'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-model', methods=['POST'])
def update_model():
    """Actualiza el modelo de IA con patrones aprendidos - SOLO ACTUALIZA EL MODELO, NO COMPILA"""
    try:
        headers = {}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        response = requests.post(
            get_api_url('/api/update-model'),
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            # NO compilar aquí - solo actualizar el modelo
            # Los clientes descargarán el modelo actualizado automáticamente
            return jsonify({
                'success': True,
                'message': 'Modelo actualizado. Los clientes descargarán automáticamente los nuevos patrones al iniciar.',
                'version': data.get('version'),
                'patterns_count': data.get('patterns_count'),
                'hashes_count': data.get('hashes_count')
            })
        return jsonify({'error': f'Error al actualizar modelo: {response.status_code}', 'details': response.text}), response.status_code
    except requests.exceptions.ConnectionError:
        error_msg = 'No se pudo conectar a la API.'
        if IS_RENDER:
            error_msg += ' En Render, asegúrate de que la API esté configurada correctamente.'
        else:
            error_msg += ' Verifica que esté corriendo en http://localhost:5000'
        return jsonify({'error': error_msg}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout al conectar con la API. La API puede estar sobrecargada.'}), 504
    except Exception as e:
        import traceback
        print(f"Error en create_token: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

@app.route('/api/learned-patterns', methods=['GET'])
def get_learned_patterns():
    """Obtiene patrones aprendidos - OPTIMIZADO: Acceso directo a BD sin HTTP"""
    import time
    
    # Caché (60 segundos TTL - los patrones no cambian tan frecuentemente)
    cache_key = 'learned_patterns'
    if cache_key in _stats_cache:
        if time.time() - _stats_cache_time.get(cache_key, 0) < 60:
            return jsonify(_stats_cache[cache_key]), 200
    
    try:
        # Acceso directo a BD (SIN HTTP - MUCHO MÁS RÁPIDO)
        with get_api_db_cursor() as cursor:
            # Verificar si la tabla existe y tiene la columna is_active
            try:
                cursor.execute('''
                    SELECT pattern_type, pattern_value, pattern_category, confidence,
                           learned_from_count, first_learned_at, is_active
                    FROM learned_patterns
                    WHERE is_active = 1
                    ORDER BY learned_from_count DESC, confidence DESC
                ''')
            except sqlite3.OperationalError:
                # Si no tiene is_active, consultar sin ese filtro
                try:
                    cursor.execute('''
                        SELECT pattern_type, pattern_value, pattern_category, confidence,
                               learned_from_count, first_learned_at, 1 as is_active
                        FROM learned_patterns
                        ORDER BY learned_from_count DESC, confidence DESC
                    ''')
                except sqlite3.OperationalError:
                    # Si la tabla no existe, retornar vacío
                    result = {'patterns': [], 'total': 0}
                    _stats_cache[cache_key] = result
                    _stats_cache_time[cache_key] = time.time()
                    return jsonify(result), 200
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'type': row[0],
                    'value': row[1],
                    'category': row[2],
                    'confidence': row[3],
                    'learned_from_count': row[4],
                    'first_learned_at': row[5],
                    'is_active': bool(row[6])
                })
            
            result = {'patterns': patterns, 'total': len(patterns)}
            
            # Guardar en caché
            _stats_cache[cache_key] = result
            _stats_cache_time[cache_key] = time.time()
            
            return jsonify(result), 200
    except Exception as e:
        import traceback
        print(f"Error en get_learned_patterns: {str(e)}")
        print(traceback.format_exc())
        # Retornar respuesta vacía en lugar de error para no romper la app
        return jsonify({'patterns': [], 'total': 0, 'error': str(e)}), 200

@app.route('/api/ai-model/latest', methods=['GET'])
def get_latest_ai_model():
    """Obtiene el modelo de IA más reciente - OPTIMIZADO: Acceso directo a BD sin HTTP"""
    import time
    
    # Caché (300 segundos TTL - el modelo no cambia tan frecuentemente)
    cache_key = 'ai_model_latest'
    if cache_key in _stats_cache:
        if time.time() - _stats_cache_time.get(cache_key, 0) < 300:
            return jsonify(_stats_cache[cache_key]), 200
    
    try:
        # Acceso directo a BD (SIN HTTP - MUCHO MÁS RÁPIDO)
        with get_api_db_cursor() as cursor:
            # Obtener patrones aprendidos
            try:
                cursor.execute('''
                    SELECT pattern_value, pattern_category, confidence, learned_from_count
                    FROM learned_patterns
                    WHERE is_active = 1
                    ORDER BY learned_from_count DESC
                ''')
            except sqlite3.OperationalError:
                cursor.execute('''
                    SELECT pattern_value, pattern_category, confidence, learned_from_count
                    FROM learned_patterns
                    ORDER BY learned_from_count DESC
                ''')
            
            patterns = {
                'high_risk': [],
                'medium_risk': [],
                'low_risk': []
            }
            
            for row in cursor.fetchall():
                pattern_value, category, confidence, count = row
                if category in patterns:
                    patterns[category].append({
                        'value': pattern_value,
                        'confidence': confidence,
                        'learned_from_count': count
                    })
            
            # Obtener hashes aprendidos
            try:
                cursor.execute('''
                    SELECT file_hash, is_hack, confirmed_count
                    FROM learned_hashes
                    WHERE is_hack = 1
                    ORDER BY confirmed_count DESC
                ''')
            except sqlite3.OperationalError:
                hashes = []
            else:
                hashes = []
                for row in cursor.fetchall():
                    hashes.append({
                        'hash': row[0],
                        'is_hack': bool(row[1]),
                        'confirmed_count': row[2]
                    })
            
            result = {
                'version': '1.0.0',
                'updated_at': None,
                'patterns': patterns,
                'hashes': hashes,
                'patterns_count': sum(len(p) for p in patterns.values()),
                'hashes_count': len(hashes)
            }
            
            # Guardar en caché
            _stats_cache[cache_key] = result
            _stats_cache_time[cache_key] = time.time()
            
            return jsonify(result), 200
    except Exception as e:
        import traceback
        print(f"Error en get_latest_ai_model: {str(e)}")
        print(traceback.format_exc())
        # Retornar modelo vacío en lugar de error
        return jsonify({
            'version': '1.0.0',
            'updated_at': None,
            'patterns': {'high_risk': [], 'medium_risk': [], 'low_risk': []},
            'hashes': [],
            'patterns_count': 0,
            'hashes_count': 0
        }), 200

@app.route('/api/generate-app', methods=['POST'])
@admin_required
def generate_app():
    """Genera una nueva versión de la aplicación - COMPILA REALMENTE EL EJECUTABLE"""
    # En Render no se puede compilar (requiere PyInstaller y herramientas de Windows)
    if IS_RENDER:
        return jsonify({
            'success': False,
            'error': 'No se puede compilar el ejecutable en Render. Debes compilarlo localmente en Windows usando PyInstaller.'
        }), 400
    
    import subprocess
    import os
    import time
    import hashlib
    from datetime import datetime
    
    def generate():
        try:
            # Paso 1: Actualizar modelo de IA primero (SIN COMPILAR)
            yield f"data: {json.dumps({'step': 'Actualizando modelo de IA con patrones aprendidos...', 'progress': 20})}\n\n"
            time.sleep(0.5)
            
            # Llamar al endpoint de actualización de modelo
            try:
                headers = {}
                if API_KEY:
                    headers['X-API-Key'] = API_KEY
                update_response = requests.post(
                    get_api_url('/api/update-model'),
                    headers=headers,
                    timeout=30
                )
                if update_response.status_code == 200:
                    model_data = update_response.json()
                    patterns_count = model_data.get('patterns_count', 0)
                    hashes_count = model_data.get('hashes_count', 0)
                    step_message = f'✅ Modelo actualizado: {patterns_count} patrones, {hashes_count} hashes. Los clientes descargarán automáticamente.'
                    yield f"data: {json.dumps({'step': step_message, 'progress': 50})}\n\n"
                else:
                    yield f"data: {json.dumps({'step': 'Advertencia: No se pudo actualizar modelo, continuando...', 'progress': 50})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'step': f'Advertencia: Error actualizando modelo: {str(e)}', 'progress': 50})}\n\n"
            
            time.sleep(0.5)
            
            # Paso 2: Compilar ejecutable (solo si se solicita explícitamente)
            yield f"data: {json.dumps({'step': 'Compilando ejecutable con PyInstaller (esto puede tardar varios minutos)...', 'progress': 60})}\n\n"
            time.sleep(0.5)
            
            # Ruta al script de compilación
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            compile_script = os.path.join(project_root, 'BAT', '01-Compilar', 'COMPILAR_FINAL.bat')
            
            yield f"data: {json.dumps({'step': f'Buscando script en: {compile_script}', 'progress': 55})}\n\n"
            
            if not os.path.exists(compile_script):
                yield f"data: {json.dumps({'step': f'ERROR: Script de compilación no encontrado en: {compile_script}', 'progress': 100, 'error': True})}\n\n"
                return
            
            yield f"data: {json.dumps({'step': f'✅ Script encontrado: {compile_script}', 'progress': 58})}\n\n"
            
            # Ejecutar compilación
            yield f"data: {json.dumps({'step': 'Ejecutando compilación (esto puede tardar varios minutos)...', 'progress': 60})}\n\n"
            
            # Cambiar al directorio del script para ejecutarlo correctamente
            compile_dir = os.path.dirname(compile_script)
            compile_script_name = os.path.basename(compile_script)
            
            # Ejecutar en segundo plano y capturar salida
            # Usar cmd.exe /c para ejecutar el .bat correctamente en Windows
            process = subprocess.Popen(
                ['cmd.exe', '/c', compile_script_name],
                cwd=compile_dir,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combinar stderr con stdout
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitorear progreso y capturar salida en tiempo real
            progress = 60
            output_lines = []
            last_update = time.time()
            
            while process.poll() is None:
                # Leer salida línea por línea
                line = process.stdout.readline()
                if line:
                    output_lines.append(line.strip())
                    # Mostrar últimas líneas importantes
                    if any(keyword in line.lower() for keyword in ['compilando', 'building', 'creating', 'success', 'error', 'completado']):
                        yield f"data: {json.dumps({'step': f'Compilando: {line.strip()[:100]}', 'progress': progress})}\n\n"
                
                # Actualizar progreso cada 3 segundos
                current_time = time.time()
                if current_time - last_update >= 3:
                    progress = min(90, progress + 2)
                    yield f"data: {json.dumps({'step': 'Compilando... (por favor espera)', 'progress': progress})}\n\n"
                    last_update = current_time
                
                time.sleep(0.5)
            
            # Leer cualquier salida restante
            remaining_output = process.stdout.read()
            if remaining_output:
                output_lines.extend(remaining_output.splitlines())
            
            # Verificar resultado
            return_code = process.returncode
            output_text = '\n'.join(output_lines)
            
            if return_code != 0:
                error_msg = output_text[-500:] if len(output_text) > 500 else output_text
                yield f"data: {json.dumps({'step': f'ERROR en compilación (código {return_code}): {error_msg}', 'progress': 100, 'error': True})}\n\n"
                return
            
            # Verificar si hay mensajes de error en la salida
            if 'error' in output_text.lower() or 'failed' in output_text.lower():
                error_msg = output_text[-500:] if len(output_text) > 500 else output_text
                yield f"data: {json.dumps({'step': f'Advertencia en compilación: {error_msg}', 'progress': 95})}\n\n"
            
            # Paso 3: Buscar ejecutable compilado
            yield f"data: {json.dumps({'step': 'Buscando ejecutable compilado...', 'progress': 92})}\n\n"
            time.sleep(0.5)
            
            exe_path = os.path.join(project_root, 'source', 'dist', 'MinecraftSSTool.exe')
            if not os.path.exists(exe_path):
                yield f"data: {json.dumps({'step': 'ERROR: Ejecutable no encontrado después de compilación', 'progress': 100, 'error': True})}\n\n"
                return
            
            # Paso 4: Calcular hash y tamaño
            yield f"data: {json.dumps({'step': 'Verificando integridad del ejecutable...', 'progress': 95})}\n\n"
            time.sleep(0.5)
            
            file_size = os.path.getsize(exe_path)
            with open(exe_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Paso 5: Copiar a carpeta de descargas
            downloads_dir = os.path.join(project_root, 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            version = datetime.now().strftime('%Y%m%d_%H%M%S')
            download_filename = f'MinecraftSSTool_v{version}.exe'
            download_path = os.path.join(downloads_dir, download_filename)
            
            import shutil
            shutil.copy2(exe_path, download_path)
            
            # Paso 6: Registrar versión en BD
            try:
                headers = {}
                if API_KEY:
                    headers['X-API-Key'] = API_KEY
                version_response = requests.post(
                    get_api_url('/api/versions'),
                    json={
                        'version': f'1.{version}',
                        'download_url': f'/download/{download_filename}',
                        'changelog': f'Versión generada automáticamente con {model_data.get("patterns_count", 0)} patrones aprendidos',
                        'file_size': file_size,
                        'file_hash': file_hash
                    },
                    headers=headers,
                    timeout=5
                )
            except:
                pass
            
            # Paso 7: Completado
            step_message = f'✅ Aplicación generada exitosamente.\n\nArchivo: {download_filename}\nTamaño: {file_size / (1024*1024):.1f} MB\nHash: {file_hash[:16]}...\n\nNOTA: Las actualizaciones de IA se descargan automáticamente sin necesidad de recompilar.'
            yield f"data: {json.dumps({'step': step_message, 'progress': 100, 'success': True, 'download_url': f'/download/{download_filename}', 'filename': download_filename})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'step': f'ERROR: {str(e)}', 'progress': 100, 'error': True})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/download/<filename>')
def download_file(filename):
    """Endpoint para descargar el ejecutable generado - OPTIMIZADO"""
    import os
    from flask import send_file
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Lista de ubicaciones posibles en orden de prioridad (optimizado)
    possible_paths = [
        os.path.join(project_root, 'downloads', filename),
        os.path.join(project_root, 'source', 'dist', filename) if filename == 'MinecraftSSTool.exe' else None,
        os.path.join(project_root, filename)
    ]
    
    # Buscar el primer archivo que exista (evita múltiples checks)
    file_path = None
    for path in possible_paths:
        if path and os.path.exists(path) and os.path.isfile(path):
            file_path = path
            break
    
    if file_path:
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': f'Archivo no encontrado: {filename}'}), 404

@app.route('/api/scans/<int:scan_id>/report-html', methods=['GET'])
@require_api_key
def get_scan_report_html(scan_id):
    """Proxy para obtener reporte HTML de un escaneo"""
    try:
        headers = {}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        response = requests.get(
            get_api_url(f'/api/scans/{scan_id}/report-html'),
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            from flask import Response
            return Response(
                response.content,
                mimetype='text/html',
                headers=response.headers
            )
        else:
            return jsonify({'error': 'Error al generar reporte'}), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'No se pudo conectar con la API. Asegúrate de que esté ejecutándose.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-latest-exe', methods=['GET'])
def get_latest_exe():
    """Obtiene el ejecutable más reciente disponible (ya compilado)"""
    import os
    from datetime import datetime
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Buscar en downloads/ primero (versiones con timestamp)
    downloads_dir = os.path.join(project_root, 'downloads')
    latest_file = None
    latest_time = 0
    latest_filename = None
    
    if os.path.exists(downloads_dir):
        try:
            for filename in os.listdir(downloads_dir):
                if filename.endswith('.exe'):
                    file_path = os.path.join(downloads_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        if file_time > latest_time:
                            latest_time = file_time
                            latest_file = file_path
                            latest_filename = filename
        except Exception as e:
            print(f"Error buscando en downloads: {e}")
    
    # Si no hay en downloads, buscar en source/dist
    if not latest_file:
        exe_path = os.path.join(project_root, 'source', 'dist', 'MinecraftSSTool.exe')
        if os.path.exists(exe_path):
            latest_file = exe_path
            latest_time = os.path.getmtime(exe_path)
            latest_filename = 'MinecraftSSTool.exe'
    
    # También buscar en la raíz del proyecto (por si se subió directamente)
    if not latest_file:
        root_exe = os.path.join(project_root, 'MinecraftSSTool.exe')
        if os.path.exists(root_exe):
            latest_file = root_exe
            latest_time = os.path.getmtime(root_exe)
            latest_filename = 'MinecraftSSTool.exe'
    
    if latest_file and os.path.exists(latest_file):
        if not latest_filename:
            latest_filename = os.path.basename(latest_file)
        file_size = os.path.getsize(latest_file)
        return jsonify({
            'success': True,
            'download_url': f'/download/{latest_filename}',
            'filename': latest_filename,
            'file_size': file_size,
            'modified_at': datetime.fromtimestamp(latest_time).isoformat()
        })
    else:
        error_msg = 'No se encontró ejecutable compilado.'
        if IS_RENDER:
            error_msg += '\n\nEl archivo .exe debe estar en GitHub en una de estas ubicaciones:\n'
            error_msg += '• source/dist/MinecraftSSTool.exe\n'
            error_msg += '• downloads/MinecraftSSTool.exe\n\n'
            error_msg += 'Pasos para solucionarlo:\n'
            error_msg += '1. Compila el .exe localmente\n'
            error_msg += '2. Ejecuta SUBIR_EXE_A_GITHUB.bat\n'
            error_msg += '3. Sube los cambios a GitHub\n'
            error_msg += '4. Render se actualizará automáticamente'
        else:
            error_msg += ' Asegúrate de que el archivo .exe esté en la carpeta downloads/, source/dist/, o en la raíz del proyecto.'
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'is_render': IS_RENDER
        }), 404

@app.route('/api/import/echo', methods=['POST'])
@login_required
def import_echo_scan():
    """Importa resultados históricos de Echo Scanner"""
    try:
        data = request.json or {}
        
        # Validar datos requeridos
        if 'echo_id' not in data:
            return jsonify({'error': 'Se requiere echo_id'}), 400
        
        # Importar usando el script
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from importar_resultados_echo import create_echo_scan, init_db_if_needed
        
        init_db_if_needed()
        scan_id = create_echo_scan(data)
        
        if scan_id:
            return jsonify({
                'success': True,
                'scan_id': scan_id,
                'message': f'Escaneo de Echo importado exitosamente con ID {scan_id}'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Error al importar el escaneo'
            }), 500
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Error inesperado: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("🌐 Iniciando aplicación web de ASPERS Projects...")
    api_url_display = os.environ.get('API_URL') or (API_BASE_URL if IS_RENDER else API_BASE_URL)
    print(f"📡 Conectado a API: {api_url_display}")
    print(f"🔑 API Key configurada: {'Sí' if API_KEY != 'change-this-in-production' else 'No (usar valor por defecto)'}")
    print("⚠️  NOTA: Asegúrate de que la API esté corriendo en http://localhost:5000")
    print("⚠️  NOTA: La API Key debe coincidir con la configurada en api_server.py")
    app.run(host='0.0.0.0', port=8080, debug=True)

