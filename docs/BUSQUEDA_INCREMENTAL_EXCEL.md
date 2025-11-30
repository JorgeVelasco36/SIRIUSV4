# 🔍 Búsqueda Incremental Tipo Excel - SIRIUS V4

**Fecha:** 30 de noviembre de 2025  
**Funcionalidad:** Búsqueda incremental que filtra paso a paso como una persona en Excel

---

## 🎯 Objetivo

Mejorar la lógica de búsqueda de SIRIUS para que funcione como una persona filtrando en Excel: aplicando filtros paso a paso hasta obtener el resultado deseado, y preguntando por características adicionales cuando es necesario.

---

## 🔄 Cómo Funciona

### Proceso de Filtrado Incremental

SIRIUS ahora sigue un proceso sistemático de filtrado cuando la búsqueda **NO es por ISIN** sino por **características del título**:

1. **Paso 1: Nemotécnico (Prioridad Máxima)**
   - Si el usuario proporciona un nemotécnico, SIRIUS lo busca primero
   - Esto es lo más específico y reduce significativamente los resultados

2. **Paso 2: Fecha de Vencimiento**
   - Si hay fecha de vencimiento, se aplica como siguiente filtro
   - Permite diferencia de hasta 1 día para mayor flexibilidad

3. **Paso 3: Tasa Facial/Cupón**
   - Si hay tasa facial o cupón, se aplica como siguiente filtro
   - Permite diferencia de ±0.01% para tolerar pequeñas variaciones

4. **Paso 4: Proveedor**
   - Si se especifica proveedor (PIP o Precia), se aplica como filtro adicional

---

### Generación Inteligente de Preguntas

Si después de aplicar todos los filtros disponibles, SIRIUS encuentra **más de 1 resultado**, analiza qué características están disponibles en los resultados pero no se han usado como filtro, y genera preguntas prioritarias:

**Orden de Prioridad para Preguntas:**

1. **ISIN** - Si hay múltiples títulos (ISINs diferentes)
2. **Fecha de Vencimiento** - Si hay múltiples fechas de vencimiento
3. **Tasa Facial/Cupón** - Si hay múltiples tasas faciales
4. **Emisor** - Si hay múltiples emisores
5. **Proveedor** - Si hay datos de ambos proveedores

---

## 📊 Ejemplo de Flujo

### Escenario 1: Búsqueda con Nemotécnico y Fecha

**Usuario:** "¿Cuál es la TIR de un CDTBGAS0V con vencimiento el 30/08/2027?"

**Proceso de SIRIUS:**

1. **Paso 1 - Nemotécnico:**
   - Filtra por nemotécnico: `CDTBGAS0V`
   - Encuentra: 4 títulos (COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3, COB13CD2IIA0)

2. **Paso 2 - Fecha de Vencimiento:**
   - Aplica filtro por fecha: `30/08/2027` (tolerancia ±1 día)
   - Encuentra: 4 títulos (todos tienen esa fecha de vencimiento)

3. **Resultado:**
   - Como hay 4 títulos, SIRIUS pregunta: "¿Cuál es el código ISIN del título? Por ejemplo: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3 u otro (hay 4 títulos diferentes)"

---

### Escenario 2: Refinamiento Incremental

**Usuario:** "¿Cuál es la TIR de un CDTBGAS0V con vencimiento el 30/08/2027?"

**SIRIUS:** "Se encontraron 4 títulos que coinciden con tu búsqueda. Para acotar los resultados y darte la información precisa, necesito más detalles:
• ¿Cuál es el código ISIN del título? Por ejemplo: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3 u otro (hay 4 títulos diferentes)"

**Usuario:** "El que tiene tasa facial del 14,2232%"

**Proceso de SIRIUS:**

1. **Detecta refinamiento:**
   - SIRIUS reconoce que el usuario está proporcionando una característica adicional
   - Toma los 4 resultados previos (del contexto)

2. **Aplica filtro de tasa facial:**
   - Filtra los 4 títulos por cupón: `14.2232%` (tolerancia ±0.01%)
   - Encuentra: 1 título (COB13CD1K3N4)

3. **Resultado:**
   - Muestra la información del título encontrado con datos de ambos proveedores

---

## 🔑 Características Principales

### 1. Priorización de Filtros

Los filtros se aplican en este orden específico para maximizar la eficiencia:

1. **Nemotécnico** → Más específico, reduce drásticamente los resultados
2. **Fecha de Vencimiento** → Muy específica, reduce significativamente
3. **Tasa Facial/Cupón** → Específica, reduce moderadamente
4. **Proveedor** → Reduce por la mitad (dos proveedores)

### 2. Análisis de Características Disponibles

Antes de preguntar por más información, SIRIUS analiza:

- Qué características están presentes en los resultados encontrados
- Qué características **NO** se han usado como filtro aún
- Cuál característica faltante sería más efectiva para reducir los resultados

### 3. Preguntas Inteligentes y Priorizadas

SIRIUS genera preguntas basadas en:

- **Efectividad:** Qué característica reducirá más los resultados
- **Disponibilidad:** Qué características están presentes en los resultados
- **Relevancia:** Qué característica es más útil para el usuario

### 4. Mantenimiento de Contexto Conversacional

Durante todo el proceso:

- SIRIUS recuerda la búsqueda anterior
- Mantiene los resultados encontrados en memoria
- Permite que el usuario agregue características adicionales en mensajes subsiguientes
- Refina la búsqueda sobre los resultados previos, no busca desde cero

---

## 💻 Implementación Técnica

### Función Principal: `_incremental_search_by_characteristics`

**Ubicación:** `backend/services/chat_service.py`

**Funcionalidad:**
- Aplica filtros paso a paso según la prioridad
- Registra qué filtros se han aplicado
- Retorna los resultados después de todos los filtros

**Filtros Auxiliares:**
- `_filter_by_fecha_vencimiento`: Filtra con tolerancia de ±1 día
- `_filter_by_cupon`: Filtra con tolerancia de ±0.01%

### Función de Análisis: `_analyze_available_characteristics`

**Funcionalidad:**
- Analiza qué características están disponibles en los resultados
- Identifica qué características NO se han usado como filtro
- Retorna información estructurada para generar preguntas inteligentes

### Función Mejorada: `_generate_refinement_questions`

**Funcionalidad:**
- Usa el análisis de características disponibles
- Genera preguntas prioritarias basadas en efectividad
- Muestra ejemplos concretos de los valores disponibles

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Búsqueda Completa

```
Usuario: "¿Cuál es la TIR de un CDTBGAS0V con vencimiento el 30/08/2027?"

SIRIUS: 
📊 Búsqueda incremental:
  🔹 Paso 1: Filtrando por nemotécnico: CDTBGAS0V
     ✅ Después de nemotécnico: 4 resultados
  🔹 Paso 2: Filtrando por fecha de vencimiento: 30/08/2027
     ✅ Después de fecha de vencimiento: 4 → 4 resultados
  
Resultado: "Se encontraron 4 títulos que coinciden con tu búsqueda. 
Para acotar los resultados y darte la información precisa, necesito más detalles:
• ¿Cuál es el código ISIN del título? Por ejemplo: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3 u otro"
```

### Ejemplo 2: Refinamiento

```
Usuario: "La tasa facial es del 14,2232%"

SIRIUS:
🔄 Refinamiento detectado: filtrando 4 resultados previos por cupón/tasa facial
  🔹 Paso 3: Filtrando por tasa facial/cupón: 14.2232%
     ✅ Filtrado por cupón 14.2232: 4 → 1 resultados

Resultado: Muestra información del título encontrado (COB13CD1K3N4)
```

### Ejemplo 3: Búsqueda Solo por Fecha

```
Usuario: "¿Qué títulos vencen el 30/08/2027?"

SIRIUS:
📊 Búsqueda incremental:
  🔹 Paso 1: No hay nemotécnico, buscando por otras características disponibles...
     ✅ Resultados iniciales: 50 resultados
  🔹 Paso 2: Filtrando por fecha de vencimiento: 30/08/2027
     ✅ Después de fecha de vencimiento: 50 → 10 resultados

Resultado: "Se encontraron 10 títulos que coinciden con tu búsqueda..."
```

---

## 🎯 Ventajas

### Para el Usuario

1. **Más Conversacional:** Puede proporcionar información de forma gradual
2. **Más Inteligente:** SIRIUS pregunta por lo que realmente ayuda a reducir resultados
3. **Más Flexible:** No necesita tener toda la información desde el inicio
4. **Más Eficiente:** Filtra paso a paso, evitando búsquedas demasiado amplias

### Para el Sistema

1. **Mejor Rendimiento:** Filtra de forma incremental, evitando consultas muy amplias
2. **Mejor Precisión:** Aplica filtros en orden de efectividad
3. **Mejor Experiencia:** Genera preguntas más útiles y específicas
4. **Mejor Contexto:** Mantiene la conversación y permite refinamientos naturales

---

## 🔧 Detalles Técnicos

### Tolerancias de Filtrado

- **Fecha de Vencimiento:** ±1 día (para manejar pequeñas diferencias en formato o interpretación)
- **Tasa Facial/Cupón:** ±0.01% (para tolerar pequeñas variaciones de redondeo)

### Límites de Resultados

- Si hay **1 resultado único** → Muestra directamente (busca en ambos proveedores)
- Si hay **2-5 resultados** → Pregunta por más características para reducir
- Si hay **más de 5 resultados** → Pregunta por más características o muestra los primeros

---

## 📚 Archivos Modificados

1. **`backend/services/chat_service.py`**:
   - Nueva función: `_incremental_search_by_characteristics()`
   - Nueva función: `_analyze_available_characteristics()`
   - Nuevas funciones auxiliares: `_filter_by_fecha_vencimiento()`, `_filter_by_cupon()`
   - Función mejorada: `_generate_refinement_questions()`
   - Lógica modificada: `generate_response()` para detectar búsquedas por características

---

*Última actualización: 30 de noviembre de 2025*

