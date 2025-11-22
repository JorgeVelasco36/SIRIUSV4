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
let supabaseCredentials = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
});

// Verificar autenticación al cargar
function checkAuthentication() {
    // Verificar si hay credenciales guardadas en sessionStorage
    const savedCredentials = sessionStorage.getItem('supabase_credentials');
    
    if (savedCredentials) {
        try {
            supabaseCredentials = JSON.parse(savedCredentials);
            // Verificar que las credenciales sigan siendo válidas
            validateCredentials(supabaseCredentials.email, supabaseCredentials.password);
        } catch (e) {
            // Si hay error, mostrar modal de autenticación
            showAuthModal();
        }
    } else {
        // No hay credenciales guardadas, mostrar modal
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
    
    // Prevenir que Enter en los campos cierre el modal
    if (authEmail && authPassword) {
        authEmail.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                authPassword.focus();
            }
        });
        
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
    
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    if (!email || !password) {
        showAuthError('Por favor, completa todos los campos');
        return;
    }
    
    // Deshabilitar botón y mostrar loading
    submitBtn.disabled = true;
    submitText.style.display = 'none';
    submitLoading.style.display = 'flex';
    errorDiv.style.display = 'none';
    
    try {
        await validateCredentials(email, password);
    } catch (error) {
        // El error ya se maneja en validateCredentials
    } finally {
        // Restaurar botón
        submitBtn.disabled = false;
        submitText.style.display = 'inline';
        submitLoading.style.display = 'none';
    }
}

// Validar credenciales con el backend
async function validateCredentials(email, password) {
    const errorDiv = document.getElementById('auth-error');
    
    try {
        const response = await fetch(`${API_URL}/auth/supabase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Autenticación exitosa
            isAuthenticated = true;
            supabaseCredentials = { email, password };
            
            // Guardar credenciales en sessionStorage
            sessionStorage.setItem('supabase_credentials', JSON.stringify(supabaseCredentials));
            
            // Ocultar modal y mostrar aplicación
            hideAuthModal();
        } else {
            // Error de autenticación
            showAuthError(data.message || 'Error de autenticación. Por favor, verifica tu correo y contraseña.');
        }
    } catch (error) {
        console.error('Error en autenticación:', error);
        showAuthError('Error de conexión. Por favor, verifica tu conexión a internet e intenta nuevamente.');
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
        
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: messageText,
                user: 'web_user'
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
        
        // Headers
        const firstItem = data[0];
        const keys = Object.keys(firstItem);
        keys.forEach(key => {
            if (key !== 'id' && key !== 'timestamp_ingesta') {
                html += `<th>${formatKey(key)}</th>`;
            }
        });
        html += '</tr></thead><tbody>';
        
        // Rows
        data.forEach(item => {
            html += '<tr>';
            keys.forEach(key => {
                if (key !== 'id' && key !== 'timestamp_ingesta') {
                    const value = item[key];
                    const formatted = formatValue(value);
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
        'tasa': 'Tasa',
        'duracion': 'Duración',
        'convexidad': 'Convexidad',
        'emisor': 'Emisor',
        'tipo_instrumento': 'Tipo Instrumento'
    };
    return keyMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';
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



