# 🔧 Corrección: SIRIUS no mantiene contexto de conversación entre requests

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** SIRIUS no mantiene el contexto de conversación entre requests. Cuando el usuario pide mostrar resultados encontrados, muestra todos los títulos o interpreta palabras como nemotécnicos.

---

## 🐛 Problema Identificado

### Problema Principal: Pérdida de Contexto Entre Requests

**Causa raíz:** El `ChatService` se creaba en cada request HTTP, lo que significaba que `last_query`, `last_results`, y `last_query_params` se perdían entre llamadas.

```python
# ANTES (en main.py):
chat_service = ChatService(db, supabase_access_token=access_token)
```

Cada vez que se hacía una petición, se creaba una nueva instancia, perdiendo todo el contexto.

### Problemas Específicos:

1. **"RESULTADO" interpretado como nemotécnico:**
   - Usuario: "¿Cuál es la tir de valoración del resultado encontrado?"
   - SIRIUS: "No se encontraron valoraciones para el nemotécnico RESULTADO.."

2. **Muestra todos los títulos en lugar del encontrado:**
   - Usuario encuentra 1 título
   - Usuario: "Entregame la información del título encontrado"
   - SIRIUS: Muestra 3250 títulos en lugar de solo el 1 encontrado

---

## ✅ Correcciones Implementadas

### 1. Almacenamiento de Contexto en Memoria

**Archivo:** `backend/main.py`

Se implementó un sistema de almacenamiento de contexto por usuario/sesión:

```python
# Almacenamiento de contexto de conversación por usuario/sesión
conversation_contexts: Dict[str, Dict] = {}
context_lock = threading.Lock()  # Lock para acceso thread-safe
```

**Características:**
- Almacena contexto por usuario (o "default" si no hay usuario)
- Thread-safe usando locks
- Se mantiene entre requests

---

### 2. Modificación de ChatService para Aceptar Contexto

**Archivo:** `backend/services/chat_service.py`

Se modificó el constructor de `ChatService` para aceptar contexto existente:

```python
def __init__(self, db: Session, supabase_access_token: Optional[str] = None, 
             conversation_context: Optional[Dict] = None):
    # ...
    if conversation_context:
        self.last_query = self._deserialize_query(conversation_context.get("last_query_dict"))
        self.last_results = self._deserialize_results(conversation_context.get("last_results_dict"))
        self.last_query_params = conversation_context.get("last_query_params")
```

**Métodos agregados:**
- `get_conversation_context()`: Serializa el contexto actual
- `_serialize_query()`: Convierte ValuationQuery a diccionario
- `_deserialize_query()`: Convierte diccionario a ValuationQuery
- `_serialize_results()`: Convierte lista de Valuation a lista de diccionarios
- `_deserialize_results()`: Convierte lista de diccionarios a lista de diccionarios (mantiene como dict)

---

### 3. Modificación del Endpoint /chat

**Archivo:** `backend/main.py`

El endpoint ahora:
1. Obtiene el contexto previo del usuario
2. Crea ChatService con el contexto
3. Procesa la consulta
4. Guarda el nuevo contexto

```python
@app.post(f"{settings.api_v1_prefix}/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    user_id = message.user or "default"
    
    # Obtener contexto previo (thread-safe)
    with context_lock:
        context = conversation_contexts.get(user_id)
    
    # Crear servicio con contexto
    chat_service = ChatService(db, conversation_context=context)
    response = chat_service.generate_response(message.message, message.user)
    
    # Guardar nuevo contexto (thread-safe)
    with context_lock:
        conversation_contexts[user_id] = chat_service.get_conversation_context()
    
    return ChatResponse(**response)
```

---

### 4. Agregado "RESULTADO" a Palabras Comunes

**Archivo:** `backend/services/chat_service.py`

Se agregó "RESULTADO" y variaciones a la lista de palabras comunes para evitar interpretación como nemotécnico:

```python
'RESULTADO', 'RESULTADOS', 'RESULTADA', 'RESULTADAS',  # Palabras relacionadas con resultado
```

---

### 5. Helper para Manejar Objetos y Diccionarios

**Archivo:** `backend/services/chat_service.py`

Se agregó función helper para trabajar con objetos Valuation y diccionarios:

```python
def _get_valuation_field(self, v, field: str):
    """Helper para obtener un campo de una valoración (objeto o diccionario)"""
    if isinstance(v, dict):
        return v.get(field)
    return getattr(v, field, None)
```

Esto permite que el código funcione tanto con objetos Valuation como con diccionarios (cuando vienen del contexto deserializado).

---

## 🔄 Flujo de Contexto

### Antes:
```
Request 1: Usuario pregunta → ChatService creado → last_results = [título1]
Request 2: Usuario pide mostrar → ChatService creado NUEVO → last_results = None ❌
```

### Después:
```
Request 1: Usuario pregunta → ChatService creado → last_results = [título1]
          → Contexto guardado en conversation_contexts[user_id]

Request 2: Usuario pide mostrar → Contexto cargado → ChatService con contexto
          → last_results = [título1] ✅ → Muestra solo el título encontrado
```

---

## 📝 Limitaciones y Consideraciones

### Limitaciones Actuales:

1. **Almacenamiento en Memoria:**
   - El contexto se pierde al reiniciar el servidor
   - No es compartido entre múltiples instancias del servidor
   - **Solución futura:** Migrar a Redis o base de datos

2. **Serialización de Objetos:**
   - Los objetos Valuation se convierten a diccionarios
   - Algunas funciones pueden necesitar ajustes para trabajar con diccionarios
   - **Solución actual:** Helper `_get_valuation_field()` para acceso uniforme

3. **Memoria:**
   - Los resultados se almacenan completamente en memoria
   - Para muchos usuarios, podría ser necesario limitar el tamaño o TTL
   - **Solución futura:** Limpiar contexto después de X minutos de inactividad

---

## 🧪 Escenarios de Prueba

### Escenario 1: Mantener Contexto Entre Requests

1. **Request 1:** "¿Cuál es la TIR de valoración de un CDTBBOS0V con vencimiento del 02/02/2027?"
   - SIRIUS encuentra 1 título
   - Contexto guardado: `{last_query: {...}, last_results: [título1]}`

2. **Request 2:** "Muéstrame la información del título que encontraste"
   - SIRIUS carga contexto previo
   - Muestra solo el título encontrado (1 título)

**Resultado esperado:** ✅ Funciona correctamente

---

### Escenario 2: No Interpretar "RESULTADO" como Nemotécnico

**Request:** "¿Cuál es la tir de valoración del resultado encontrado?"
- SIRIUS NO interpreta "RESULTADO" como nemotécnico
- Reconoce que es parte de una frase
- Usa el contexto previo para mostrar el resultado

**Resultado esperado:** ✅ Funciona correctamente

---

### Escenario 3: Mostrar Solo Resultados Encontrados

**Request:** "Entregame la información del título encontrado"
- SIRIUS usa `last_results` del contexto
- Muestra solo los resultados de la consulta anterior
- NO ejecuta nueva búsqueda

**Resultado esperado:** ✅ Muestra solo los títulos encontrados previamente

---

## 🎯 Mejoras Futuras

1. **Persistencia del Contexto:**
   - Migrar a Redis para almacenamiento distribuido
   - O almacenar en base de datos con TTL

2. **Limpieza Automática:**
   - Eliminar contexto después de X minutos de inactividad
   - Limitar tamaño de resultados almacenados

3. **Múltiples Conversaciones:**
   - Permitir múltiples hilos de conversación por usuario
   - Identificar conversaciones por ID de sesión

---

*Última actualización: 29 de noviembre de 2025*

