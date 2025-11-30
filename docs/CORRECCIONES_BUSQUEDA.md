# 🔧 Correcciones a la Lógica de Búsqueda de SIRIUS

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** SIRIUS no entiende refinamientos de búsqueda y confunde campos con nemotécnicos

---

## 🐛 Problemas Identificados

### Problema 1: Confusión entre campos y nemotécnicos

**Ejemplo del problema:**
- Usuario pregunta: "La tasa facial o cupón del título que estoy buscando es de 17,87%"
- SIRIUS interpreta "FACIAL" como un nemotécnico
- Responde: "No se encontraron valoraciones para el nemotécnico FACIAL.."
- **Causa:** El sistema no reconocía que "FACIAL" es parte de "tasa facial" (un campo), no un nemotécnico

### Problema 2: Refinamiento de búsqueda no funciona

**Ejemplo del problema:**
- Primera consulta: "¿Cuál es la TIR de valoración de un CDTBBOS0V con vencimiento del 02/02/2027?"
- SIRIUS encuentra 2 títulos (pero dice que son 2 cuando en realidad es 1)
- Segunda consulta: "La tasa facial o cupón del título que estoy buscando es de 17,87%"
- SIRIUS NO entiende que debe buscar entre los 2 títulos previos y filtrar por cupón
- En su lugar, busca "FACIAL" como nemotécnico

### Problema 3: Conteo incorrecto de resultados

- Cuando encuentra 1 título con múltiples valoraciones (diferentes proveedores o fechas), dice que son 2 títulos

---

## ✅ Correcciones Implementadas

### 1. Agregado "FACIAL" a palabras comunes

**Archivo:** `backend/services/chat_service.py`

Se agregó "FACIAL" a la lista de palabras comunes que NO deben interpretarse como nemotécnicos:

```python
palabras_comunes = [
    # ... otras palabras ...
    'FACIAL', 'CUPON', 'CUPÓN', 'TASA', 'BANCO', 'BANCARIO'  # Campos y términos financieros comunes
]
```

**Resultado:** Ahora "FACIAL" no se interpreta como nemotécnico cuando forma parte de "tasa facial".

---

### 2. Mejorada detección de refinamiento de búsqueda

**Archivo:** `backend/services/chat_service.py` (línea ~331)

Se mejoró la lógica para detectar cuando el usuario está refinando una búsqueda anterior:

```python
mensaje_es_refinamiento = (
    self.last_query and 
    not extracted.get("nemotecnico") and 
    not extracted.get("_nemotecnico") and
    not extracted.get("isins") and
    (cupon is not None or "cupon" in message_lower or "tasa facial" in message_lower or "tasa del" in message_lower)
)
```

**Resultado:** Cuando el usuario proporciona información adicional (como cupón/tasa facial), el sistema:
- Mantiene los filtros de la búsqueda anterior (nemotécnico, fecha de vencimiento, etc.)
- Agrega el nuevo filtro (cupón)
- Busca usando todos los filtros combinados

---

### 3. Mejorado mensaje de error cuando se confunde campo con nemotécnico

**Archivo:** `backend/services/chat_service.py` (línea ~570)

Se agregó validación para detectar cuando se interpreta incorrectamente un campo como nemotécnico:

```python
if nemotecnico.upper() in ['FACIAL', 'CUPON', 'CUPÓN', 'TASA', 'BANCO']:
    answer = f"No se encontraron valoraciones. Parece que '{nemotecnico}' podría ser parte de un campo (como 'tasa facial' o 'cupón') en lugar de un nemotécnico."
    # ... recomendaciones específicas ...
```

**Resultado:** Mensaje más claro cuando el sistema detecta que podría haber confundido un campo con un nemotécnico.

---

### 4. Corregido conteo de títulos únicos

**Archivo:** `backend/services/chat_service.py` (línea ~533)

Se cambió el conteo para contar títulos únicos por ISIN en lugar de valoraciones totales:

```python
# Contar títulos únicos por ISIN para mostrar el número correcto
isins_unicos = set(v.isin for v in valuations if v.isin)
num_titulos = len(isins_unicos)
```

**Resultado:** Cuando hay 1 título con valoraciones de múltiples proveedores, ahora dice "1 título" en lugar de "2 títulos".

---

### 5. Mejorado manejo de refinamiento sin resultados

**Archivo:** `backend/services/chat_service.py` (línea ~563)

Se agregó lógica especial para cuando un refinamiento no encuentra resultados:

```python
es_refinamiento_sin_resultados = (
    self.last_results and 
    len(self.last_results) > 0 and
    query.cupon is not None
)
```

**Resultado:** Mensaje más claro cuando se refina una búsqueda anterior pero no hay resultados que cumplan todos los criterios.

---

## 🧪 Escenarios de Prueba

### Escenario 1: Búsqueda inicial por nemotécnico

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBBOS0V con vencimiento del 02/02/2027?"

**Resultado esperado:**
- SIRIUS encuentra títulos con nemotécnico "CDTBBOS0V" y vencimiento 02/02/2027
- Si hay múltiples resultados, pregunta por información adicional para refinar
- Muestra el conteo correcto de títulos únicos

### Escenario 2: Refinamiento con tasa facial

**Consulta previa:** Encuentra 2 títulos  
**Consulta de refinamiento:** "La tasa facial o cupón del título que estoy buscando es de 17,87%"

**Resultado esperado:**
- SIRIUS mantiene los filtros anteriores (nemotécnico, fecha de vencimiento)
- Agrega el filtro de cupón (17.87%)
- Busca entre los títulos encontrados previamente
- Filtra por cupón y muestra solo el título que cumple todos los criterios
- NO interpreta "FACIAL" como nemotécnico

### Escenario 3: Refinamiento sin resultados

**Consulta previa:** Encuentra 2 títulos  
**Consulta de refinamiento:** "La tasa facial es del 20%"

**Resultado esperado (si ningún título tiene 20%):**
- Mensaje claro indicando que se encontraron títulos con los criterios iniciales
- Explica que ninguno cumple con el filtro adicional (cupón 20%)
- Sugiere verificar el valor del cupón o ver todos los resultados iniciales

---

## 📝 Notas de Implementación

1. **Contexto de conversación:** El sistema ahora mantiene mejor el contexto entre consultas usando `self.last_query` y `self.last_results`.

2. **Extracción de cupón:** Se mejoró la detección de valores de cupón/tasa facial en el mensaje usando múltiples patrones regex.

3. **Palabras comunes:** Se expandió la lista de palabras que NO son nemotécnicos para incluir términos financieros comunes.

4. **Logging:** Se agregaron más logs para facilitar el debugging de problemas de búsqueda.

---

## 🔄 Próximos Pasos Sugeridos

1. **Pruebas adicionales:** Probar con diferentes variaciones de consultas de refinamiento
2. **Mejora de mensajes:** Revisar mensajes de error para que sean aún más claros
3. **Optimización:** Evaluar si se puede mejorar la velocidad de búsqueda cuando hay muchos resultados

---

*Última actualización: 29 de noviembre de 2025*

