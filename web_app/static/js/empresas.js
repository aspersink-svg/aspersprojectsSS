/**
 * Funciones de gestión de empresas - ASPERS Projects
 */

// ============================================================
// GESTIÓN DE EMPRESAS
// ============================================================

async function loadCompanyInfo() {
    try {
        const response = await fetch('/api/company/info');
        const data = await response.json();
        
        const card = document.getElementById('company-info-card');
        if (!card) return;
        
        if (data.success && data.company) {
            const company = data.company;
            const usedUsers = company.current_users || 0;
            const maxUsers = company.max_users || 8;
            const usedAdmins = company.current_admins || 0;
            const maxAdmins = company.max_admins || 3;
            
            card.innerHTML = `
                <h3 class="card-title">Información de la Empresa</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
                    <div>
                        <strong>Nombre:</strong> ${company.name || 'N/A'}
                    </div>
                    <div>
                        <strong>Email de contacto:</strong> ${company.contact_email || 'N/A'}
                    </div>
                    <div>
                        <strong>Teléfono:</strong> ${company.contact_phone || 'N/A'}
                    </div>
                    <div>
                        <strong>Estado de suscripción:</strong> 
                        <span class="badge badge-${company.subscription_status === 'active' ? 'success' : 'danger'}">
                            ${company.subscription_status || 'N/A'}
                        </span>
                    </div>
                    <div>
                        <strong>Usuarios:</strong> ${usedUsers} / ${maxUsers}
                        <div style="width: 100%; background: #1e2329; border-radius: 4px; height: 8px; margin-top: 4px;">
                            <div style="width: ${(usedUsers / maxUsers) * 100}%; background: ${usedUsers >= maxUsers ? '#ef4444' : '#10b981'}; height: 100%; border-radius: 4px;"></div>
                        </div>
                    </div>
                    <div>
                        <strong>Administradores:</strong> ${usedAdmins} / ${maxAdmins}
                        <div style="width: 100%; background: #1e2329; border-radius: 4px; height: 8px; margin-top: 4px;">
                            <div style="width: ${(usedAdmins / maxAdmins) * 100}%; background: ${usedAdmins >= maxAdmins ? '#ef4444' : '#3b82f6'}; height: 100%; border-radius: 4px;"></div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            card.innerHTML = '<div class="loading-cell">Error al cargar información de la empresa</div>';
        }
    } catch (error) {
        console.error('Error cargando información de empresa:', error);
        const card = document.getElementById('company-info-card');
        if (card) {
            card.innerHTML = '<div class="loading-cell">Error al cargar información de la empresa</div>';
        }
    }
}

async function loadCompanyTokens() {
    try {
        const response = await fetch('/api/company/registration-tokens?include_used=false');
        const data = await response.json();
        
        const tbody = document.getElementById('company-tokens-table-body');
        if (!tbody) return;
        
        if (data.success && data.tokens && data.tokens.length > 0) {
            tbody.innerHTML = data.tokens.map(token => {
                const createdDate = new Date(token.created_at);
                const expiresDate = token.expires_at ? new Date(token.expires_at) : null;
                const isExpired = expiresDate && expiresDate < new Date();
                const tokenSnippet = token.token.substring(0, 20) + '...';
                const tokenType = token.is_admin_token ? 'Admin' : 'Usuario';
                
                return `
                    <tr>
                        <td><code style="font-size: 12px;">${tokenSnippet}</code></td>
                        <td><span class="badge badge-${token.is_admin_token ? 'info' : 'success'}">${tokenType}</span></td>
                        <td>${createdDate.toLocaleString('es-ES')}</td>
                        <td>
                            ${expiresDate ? expiresDate.toLocaleString('es-ES') : 'Sin expiración'}
                            ${isExpired ? '<span class="badge badge-danger">Expirado</span>' : ''}
                        </td>
                        <td>
                            <span class="badge badge-${token.is_used ? 'danger' : 'success'}">
                                ${token.is_used ? 'Usado' : 'Activo'}
                            </span>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">No hay tokens de registro</td></tr>';
        }
    } catch (error) {
        console.error('Error cargando tokens de empresa:', error);
        const tbody = document.getElementById('company-tokens-table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">Error al cargar tokens</td></tr>';
        }
    }
}

async function loadCompanyUsers() {
    try {
        const response = await fetch('/api/company/users');
        const data = await response.json();
        
        const tbody = document.getElementById('company-users-table-body');
        if (!tbody) return;
        
        if (data.success && data.users && data.users.length > 0) {
            tbody.innerHTML = data.users.map(user => {
                const lastLogin = user.last_login ? new Date(user.last_login).toLocaleString('es-ES') : 'Nunca';
                const roles = user.roles || [];
                const roleBadges = roles.map(role => {
                    if (role === 'admin') return '<span class="badge badge-warning">Admin</span>';
                    if (role === 'administrador') return '<span class="badge badge-info">Admin Empresa</span>';
                    if (role === 'empresa') return '<span class="badge badge-success">Empresa</span>';
                    if (role === 'staff') return '<span class="badge badge-success">Staff</span>';
                    return `<span class="badge badge-secondary">${role}</span>`;
                }).join(' ');
                
                return `
                    <tr>
                        <td>${user.username}</td>
                        <td>${user.email || 'N/A'}</td>
                        <td>${roleBadges}</td>
                        <td>${lastLogin}</td>
                        <td>
                            <span class="badge badge-${user.is_active ? 'success' : 'danger'}">
                                ${user.is_active ? 'Activo' : 'Inactivo'}
                            </span>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">No hay usuarios en la empresa</td></tr>';
        }
    } catch (error) {
        console.error('Error cargando usuarios de empresa:', error);
        const tbody = document.getElementById('company-users-table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">Error al cargar usuarios</td></tr>';
        }
    }
}

function setupCompanyListeners() {
    // Formulario de token de registro de empresa
    const companyTokenForm = document.getElementById('company-registration-token-form');
    if (companyTokenForm) {
        companyTokenForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const description = document.getElementById('company-reg-token-description').value;
            const expiresHours = parseInt(document.getElementById('company-reg-token-expires').value) || 24;
            const isAdminToken = document.getElementById('company-reg-token-is-admin').checked;
            
            try {
                const response = await fetch('/api/company/registration-tokens', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        description: description,
                        expires_hours: expiresHours,
                        is_admin_token: isAdminToken
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const resultDiv = document.getElementById('company-registration-token-result');
                    const tokenCode = document.getElementById('generated-company-registration-token');
                    
                    if (resultDiv && tokenCode) {
                        tokenCode.textContent = data.token;
                        resultDiv.style.display = 'block';
                        companyTokenForm.reset();
                        document.getElementById('company-reg-token-expires').value = 24;
                        loadCompanyTokens();
                    }
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            } catch (error) {
                console.error('Error creando token de empresa:', error);
                alert('Error al crear token de registro');
            }
        });
    }
    
    // Botón copiar token de empresa
    const copyCompanyTokenBtn = document.getElementById('copy-company-registration-token-btn');
    if (copyCompanyTokenBtn) {
        copyCompanyTokenBtn.addEventListener('click', function() {
            const tokenCode = document.getElementById('generated-company-registration-token');
            if (tokenCode) {
                const token = tokenCode.textContent;
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(token).then(() => {
                        copyCompanyTokenBtn.textContent = '✓ Copiado';
                        setTimeout(() => {
                            copyCompanyTokenBtn.textContent = 'Copiar';
                        }, 2000);
                    });
                } else {
                    // Fallback para navegadores antiguos
                    const textarea = document.createElement('textarea');
                    textarea.value = token;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    copyCompanyTokenBtn.textContent = '✓ Copiado';
                    setTimeout(() => {
                        copyCompanyTokenBtn.textContent = 'Copiar';
                    }, 2000);
                }
            }
        });
    }
}


