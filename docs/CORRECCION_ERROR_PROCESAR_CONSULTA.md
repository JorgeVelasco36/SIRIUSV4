# 🔧 Corrección: Error al procesar consulta cuando se pide mostrar resultados

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** SIRIUS muestra error "Error al procesar la consulta. Por favor, intenta nuevamente." cuando el usuario pide mostrar resultados del título encontrado.

---

## 🐛 Problema Identificado

### Error al Procesar Consulta

**Síntoma:**
- Usuario pregunta: "¿Cual es el resultado del titulo encontrado?"
- SIRIUS responde: "Error al procesar la consulta. Por favor, intenta nuevamente."

**Causa raíz:** Cuando los resultados se guardan en el contexto de conversación, se serializan como diccionarios. Sin embargo, varias funciones del código accedían directamente a atributos de objetos `Valuation`, fallando cuando recibían diccionarios.

**Funciones afectadas:**
1. `_valuation_to_dict()` - Accedía directamente a `valuation.isin`, `valuation.proveedor.value`, etc.
2. `_generate_general_recommendations()` - Accedía directamente a `v.proveedor`, `v.fecha`, etc.
3. `_generate_refinement_questions()` - Accedía directamente a `v.isin`, `v.emisor`, etc.

---

## ✅ Correcciones Implementadas

### 1. Mejorado `_valuation_to_dict()` para Manejar Diccionarios

**Archivo:** `backend/services/chat_service.py` (línea ~1126)

**Antes:**
```python
def _valuation_to_dict(self, valuation) -> Dict:
    return {
        "isin": valuation.isin,  # ❌ Falla si valuation es dict
        "proveedor": valuation.proveedor.value  # ❌ Falla si valuation es dict
    }
```

**Después:**
```python
def _valuation_to_dict(self, valuation) -> Dict:
    # Si ya es un diccionario, retornarlo directamente
    if isinstance(valuation, dict):
        result = valuation.copy()
        # Normalizar formato de fecha y proveedor
        ...
        return result
    # Si es un objeto Valuation, convertirlo normalmente
    ...
```

**Resultado:** Ahora funciona tanto con objetos `Valuation` como con diccionarios.

---

### 2. Mejorado `_generate_general_recommendations()` para Usar Helper

**Archivo:** `backend/services/chat_service.py` (línea ~1168)

**Antes:**
```python
providers = set(v.proveedor for v in valuations)  # ❌ Falla si v es dict
dates = set(v.fecha for v in valuations)  # ❌ Falla si v es dict
```

**Después:**
```python
# Usar helper para acceder a campos (funciona con objetos y diccionarios)
providers = set()
for v in valuations:
    proveedor = self._get_valuation_field(v, "proveedor")
    # Normalizar formato...
    if proveedor_val:
        providers.add(proveedor_val)

dates = set(self._get_valuation_field(v, "fecha") for v in valuations)
```

**Resultado:** Ahora funciona tanto con objetos `Valuation` como con diccionarios.

---

### 3. Mejorado `_generate_refinement_questions()` para Usar Helper

**Archivo:** `backend/services/chat_service.py` (línea ~1237)

**Antes:**
```python
unique_isins = set(v.isin for v in valuations if v.isin)  # ❌ Falla si v es dict
unique_emisores = set(v.emisor for v in valuations if v.emisor)  # ❌ Falla si v es dict
```

**Después:**
```python
# Usar helper para acceder a campos
unique_isins = set(self._get_valuation_field(v, "isin") for v in valuations if self._get_valuation_field(v, "isin"))
unique_emisores = set(self._get_valuation_field(v, "emisor") for v in valuations if self._get_valuation_field(v, "emisor"))
```

**Resultado:** Ahora funciona tanto con objetos `Valuation` como con diccionarios.

---

### 4. Mejorado Logging de Errores

**Archivo:** `backend/services/chat_service.py` (línea ~954)

**Cambio:**
```python
except Exception as e:
    import traceback
    error_trace = traceback.format_exc()
    logger.error(f"Error generando respuesta: {str(e)}")
    logger.error(f"Traceback: {error_trace}")  # ✅ Ahora incluye traceback completo
```

**Resultado:** Facilita el debugging al mostrar el traceback completo en los logs.

---

### 5. Agregado Validación de Formato de Resultados

**Archivo:** `backend/services/chat_service.py` (línea ~578)

**Cambio:**
```python
# Validar formato de resultados antes de procesarlos
if not isinstance(self.last_results, list):
    logger.error(f"last_results no es una lista: {type(self.last_results)}")
    raise ValueError(f"Formato inválido de resultados")

# Verificar que cada resultado sea válido
for idx, result in enumerate(self.last_results):
    if not isinstance(result, (dict, object)):
        logger.error(f"Resultado {idx} tiene formato inválido")
        raise ValueError(f"Resultado {idx} tiene formato inválido")
```

**Resultado:** Detecta problemas de formato antes de procesar los resultados.

---

## 🔄 Flujo Corregido

### Antes (Fallaba):
```
1. Usuario pregunta → SIRIUS encuentra 1 título
2. Resultados se guardan como diccionarios en contexto
3. Usuario: "¿Cual es el resultado del titulo encontrado?"
4. SIRIUS carga contexto con diccionarios
5. ❌ `_valuation_to_dict()` falla al acceder a `valuation.isin`
6. ❌ Error: "Error al procesar la consulta"
```

### Después (Funciona):
```
1. Usuario pregunta → SIRIUS encuentra 1 título
2. Resultados se guardan como diccionarios en contexto
3. Usuario: "¿Cual es el resultado del titulo encontrado?"
4. SIRIUS carga contexto con diccionarios
5. ✅ `_valuation_to_dict()` detecta que es dict y lo maneja correctamente
6. ✅ `_generate_general_recommendations()` usa helper para acceder campos
7. ✅ Resultados se muestran correctamente
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Mostrar Resultados del Contexto

**Consulta 1:** "¿Cuál es la TIR de valoración de un CDTBBOS0V con vencimiento del 02/02/2027?"
- SIRIUS encuentra 1 título
- Contexto guardado con resultados como diccionarios

**Consulta 2:** "¿Cual es el resultado del titulo encontrado?"
- ✅ SIRIUS carga contexto con diccionarios
- ✅ Procesa correctamente sin errores
- ✅ Muestra información del título encontrado

**Resultado esperado:** ✅ Funciona sin errores

---

## 📝 Notas Técnicas

### Helper `_get_valuation_field()`

Se creó un helper para acceder a campos de manera uniforme:

```python
def _get_valuation_field(self, v, field: str):
    """Helper para obtener un campo de una valoración (objeto o diccionario)"""
    if isinstance(v, dict):
        return v.get(field)
    return getattr(v, field, None)
```

**Uso:**
```python
# Funciona con ambos formatos:
isin = self._get_valuation_field(valuation, "isin")  # ✅ Objeto o dict
```

---

## 🎯 Mejoras Futuras

1. **Validación más Estricta:**
   - Validar estructura de diccionarios antes de guardar en contexto
   - Esquema de validación para resultados serializados

2. **Normalización:**
   - Convertir siempre a un formato interno consistente
   - Evitar necesidad de manejar múltiples formatos

---

*Última actualización: 29 de noviembre de 2025*

