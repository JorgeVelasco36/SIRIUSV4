// S.I.R.I.U.S V4 - Frontend JavaScript
const API_URL = '/api/v1';

// Estado de la aplicación
let filters = {
    fecha: '',
    proveedor: '',
    isins: ''
};

// Estado de autenticación
let isAuthenticated = false;
let supabaseAccessToken = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
});

// Verificar autenticación al cargar
function checkAuthentication() {
    // Verificar si hay access token guardado en sessionStorage
    const savedToken = sessionStorage.getItem('supabase_access_token');
    
    if (savedToken) {
        // Usar el token guardado
        supabaseAccessToken = savedToken;
        hideAuthModal();
    } else {
        // No hay token guardado, mostrar modal
        showAuthModal();
    }
}

// Mostrar modal de autenticación
function showAuthModal() {
    const authModal = document.getElementById('auth-modal');
    const appContainer = document.getElementById('app-container');
    
    if (authModal) {
        authModal.style.display = 'flex';
    }
    if (appContainer) {
        appContainer.style.display = 'none';
    }
    
    initializeAuthListeners();
}

// Ocultar modal y mostrar aplicación
function hideAuthModal() {
    const authModal = document.getElementById('auth-modal');
    const appContainer = document.getElementById('app-container');
    
    if (authModal) {
        authModal.style.display = 'none';
    }
    if (appContainer) {
        appContainer.style.display = 'flex';
    }
    
    // Inicializar la aplicación
    initializeEventListeners();
    loadFilters();
}

// Inicializar listeners del formulario de autenticación
function initializeAuthListeners() {
    const authForm = document.getElementById('auth-form');
    const authEmail = document.getElementById('auth-email');
    const authPassword = document.getElementById('auth-password');
    
    if (authForm) {
        authForm.addEventListener('submit', handleAuthSubmit);
    }
    
    // Permitir Enter para enviar desde cualquier campo
    if (authEmail) {
        authEmail.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                authPassword?.focus();
            }
        });
    }
    
    if (authPassword) {
        authPassword.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                authForm.dispatchEvent(new Event('submit'));
            }
        });
    }
}

// Manejar envío del formulario de autenticación
async function handleAuthSubmit(e) {
    e.preventDefault();
    
    const emailInput = document.getElementById('auth-email');
    const passwordInput = document.getElementById('auth-password');
    const submitBtn = document.getElementById('auth-submit');
    const submitText = document.getElementById('auth-submit-text');
    const submitLoading = document.getElementById('auth-submit-loading');
    const errorDiv = document.getElementById('auth-error');
    
    if (!emailInput || !emailInput.value.trim()) {
        showAuthError('Por favor, ingresa tu correo electrónico');
        return;
    }
    
    if (!passwordInput || !passwordInput.value.trim()) {
        showAuthError('Por favor, ingresa tu contraseña');
        return;
    }
    
    // Mostrar estado de carga
    if (submitBtn) submitBtn.disabled = true;
    if (submitText) submitText.style.display = 'none';
    if (submitLoading) submitLoading.style.display = 'inline-flex';
    if (errorDiv) errorDiv.style.display = 'none';
    
    try {
        // Validar credenciales con el backend
        const response = await fetch(`${API_URL}/auth/supabase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: emailInput.value.trim(),
                password: passwordInput.value.trim()
            })
        });
        
        // Verificar si la respuesta es exitosa
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Error de conexión con el servidor' }));
            showAuthError(errorData.message || `Error ${response.status}: ${response.statusText}`);
            return;
        }
        
        const data = await response.json();
        console.log('Respuesta de autenticación:', data);
        
        if (data.success) {
            // Guardar access token en sessionStorage
            if (data.access_token) {
                sessionStorage.setItem('supabase_access_token', data.access_token);
                supabaseAccessToken = data.access_token;
                isAuthenticated = true;
                console.log('Autenticación exitosa, token guardado');
            } else {
                console.warn('Autenticación exitosa pero no se recibió access_token');
            }
            
            // Ocultar modal y mostrar aplicación
            hideAuthModal();
        } else {
            showAuthError(data.message || 'Error de autenticación. Por favor, verifica tu correo y contraseña.');
        }
    } catch (error) {
        console.error('Error en autenticación:', error);
        showAuthError('Error de conexión. Por favor, verifica tu conexión a internet.');
    } finally {
        // Restaurar estado del botón
        if (submitBtn) submitBtn.disabled = false;
        if (submitText) submitText.style.display = 'inline';
        if (submitLoading) submitLoading.style.display = 'none';
    }
}

// Mostrar error en el modal
function showAuthError(message) {
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Hacer scroll al error
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function initializeEventListeners() {
    // Botón enviar
    const sendButton = document.getElementById('send-button');
    const messageInput = document.getElementById('message-input');
    
    sendButton.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Filtros
    document.getElementById('fecha').addEventListener('change', (e) => {
        filters.fecha = e.target.value;
        saveFilters();
    });
    
    document.getElementById('proveedor').addEventListener('change', (e) => {
        filters.proveedor = e.target.value;
        saveFilters();
    });
    
    document.getElementById('isins').addEventListener('input', (e) => {
        filters.isins = e.target.value;
        saveFilters();
    });
    
    document.getElementById('clear-filters').addEventListener('click', () => {
        filters = { fecha: '', proveedor: '', isins: '' };
        document.getElementById('fecha').value = '';
        document.getElementById('proveedor').value = '';
        document.getElementById('isins').value = '';
        saveFilters();
    });
}

function loadFilters() {
    const saved = localStorage.getItem('sirius_filters');
    if (saved) {
        filters = JSON.parse(saved);
        document.getElementById('fecha').value = filters.fecha || '';
        document.getElementById('proveedor').value = filters.proveedor || '';
        document.getElementById('isins').value = filters.isins || '';
    }
}

function saveFilters() {
    localStorage.setItem('sirius_filters', JSON.stringify(filters));
}

async function handleSendMessage() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Agregar mensaje del usuario
    addMessage(message, true);
    messageInput.value = '';
    sendButton.disabled = true;
    messageInput.disabled = true;
    
    // Mostrar loading
    showLoading();
    
    try {
        // Construir mensaje con filtros
        let messageText = message;
        if (filters.fecha) {
            messageText += ` (fecha: ${filters.fecha})`;
        }
        if (filters.proveedor) {
            messageText += ` (proveedor: ${filters.proveedor})`;
        }
        if (filters.isins) {
            messageText += ` (ISINs: ${filters.isins})`;
        }
        
        // Obtener token de acceso de Supabase si está disponible
        const supabaseAccessToken = sessionStorage.getItem('supabase_access_token');
        
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: messageText,
                user: 'web_user',
                supabase_access_token: supabaseAccessToken
            })
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoading();
        
        // Agregar respuesta del asistente
        addMessage(data.answer, false, data.data, data.recommendations);
        
    } catch (error) {
        hideLoading();
        addMessage('Error al procesar la consulta. Por favor, intenta nuevamente.', false);
        console.error('Error:', error);
    } finally {
        sendButton.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

function addMessage(text, isUser, data = null, recommendations = null) {
    const messagesContainer = document.getElementById('messages');
    
    // Remover mensaje de bienvenida si existe
    const welcome = messagesContainer.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'message-user' : 'message-assistant'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessage(text);
    
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'message-timestamp';
    timestampDiv.textContent = new Date().toLocaleTimeString('es-CO', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timestampDiv);
    
    // Agregar datos si existen
    if (data && !isUser) {
        const dataDiv = document.createElement('div');
        dataDiv.className = 'message-data';
        dataDiv.innerHTML = formatData(data);
        messageDiv.appendChild(dataDiv);
    }
    
    // Agregar recomendaciones si existen
    if (recommendations && recommendations.length > 0 && !isUser) {
        const recDiv = document.createElement('div');
        recDiv.className = 'recommendations';
        recDiv.innerHTML = formatRecommendations(recommendations);
        messageDiv.appendChild(recDiv);
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessage(text) {
    // Convertir markdown básico a HTML
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function formatData(data) {
    if (Array.isArray(data)) {
        if (data.length === 0) return '';
        
        // Crear tabla
        let html = '<div class="valuation-table"><table><thead><tr>';
        
        // Headers (excluir campos irrelevantes)
        const firstItem = data[0];
        const keys = Object.keys(firstItem);
        const excludedKeys = ['id', 'timestamp_ingesta', 'convexidad', 'archivo_origen'];
        keys.forEach(key => {
            if (!excludedKeys.includes(key)) {
                html += `<th>${formatKey(key)}</th>`;
            }
        });
        html += '</tr></thead><tbody>';
        
        // Rows
        data.forEach(item => {
            html += '<tr>';
            keys.forEach(key => {
                if (!excludedKeys.includes(key)) {
                    const value = item[key];
                    const formatted = formatValue(value, key);
                    const className = typeof value === 'number' ? 'number' : '';
                    html += `<td class="${className}">${formatted}</td>`;
                }
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        return html;
    } else if (data && typeof data === 'object') {
        // Objeto único
        return formatData([data]);
    }
    return '';
}

function formatKey(key) {
    const keyMap = {
        'isin': 'ISIN',
        'proveedor': 'Proveedor',
        'fecha': 'Fecha',
        'precio_limpio': 'Precio Limpio',
        'precio_sucio': 'Precio Sucio',
        'tasa': 'TIR',
        'duracion': 'Duración',
        'convexidad': 'Convexidad',
        'emisor': 'Emisor',
        'tipo_instrumento': 'Tipo Instrumento'
    };
    return keyMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value, key = null) {
    if (value === null || value === undefined) return 'N/A';
    
    // Para TIR (tasa), preservar todos los decimales tal como vienen de la base de datos
    if (key === 'tasa') {
        if (typeof value === 'number') {
            // Usar toFixed con 6 decimales para preservar precisión completa
            // Esto evitará redondeo y preservará todos los decimales significativos
            let formatted = value.toFixed(6);
            // Eliminar ceros finales innecesarios, pero preservar los decimales significativos
            formatted = formatted.replace(/\.?0+$/, '');
            // Si quedó sin decimales, agregar .000
            if (!formatted.includes('.')) {
                formatted = formatted + '.000';
            }
            return formatted;
        }
        // Si viene como string, devolverlo tal cual
        return String(value);
    }
    
    if (typeof value === 'number') {
        if (value % 1 === 0) return value.toFixed(0);
        return value.toFixed(2);
    }
    return String(value);
}

function formatRecommendations(recommendations) {
    let html = '<h4>Recomendaciones:</h4><ul>';
    recommendations.forEach(rec => {
        html += `<li>${rec}</li>`;
    });
    html += '</ul>';
    return html;
}

function showLoading() {
    const messagesContainer = document.getElementById('messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-message';
    loadingDiv.id = 'loading-message';
    loadingDiv.innerHTML = '<div class="loading-spinner"></div><span>Procesando consulta...</span>';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideLoading() {
    const loading = document.getElementById('loading-message');
    if (loading) {
        loading.remove();
    }
}



