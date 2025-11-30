# 🔧 Corrección: SIRIUS no reconoce títulos en búsquedas nuevas

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** SIRIUS no está reconociendo títulos con las características proporcionadas en búsquedas nuevas. Antes de las últimas modificaciones sí funcionaba.

---

## 🐛 Problema Identificado

### Búsquedas Nuevas Bloqueadas

**Síntoma:**
- Usuario pregunta: "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
- SIRIUS responde: "No se encontraron valoraciones para el nemotécnico CDTBBOSOV."

**Causa:** La detección de "acción de mostrar" estaba siendo demasiado agresiva y estaba interceptando búsquedas nuevas que deberían ejecutarse normalmente.

---

## ✅ Correcciones Implementadas

### 1. Validación de Búsquedas Nuevas

**Archivo:** `backend/services/chat_service.py` (línea ~575)

Se agregó validación para detectar cuando una consulta es una búsqueda nueva (no una acción de mostrar):

```python
# IMPORTANTE: Verificar si es una búsqueda nueva antes de tratar como acción de mostrar
# Si la consulta tiene palabras clave de búsqueda nueva, NO es acción de mostrar
tiene_palabras_busqueda_nueva = any(palabra in message_lower for palabra in [
    "cuál es", "cual es", "cuál es la", "cual es la", 
    "quiero saber", "necesito", "valoración de un", "valoracion de un",
    "tir de valoración", "precio de", "con vencimiento"
])

# Si tiene palabras clave de búsqueda nueva, NO es acción de mostrar
if tiene_palabras_busqueda_nueva:
    es_accion_mostrar = False
    logger.info("Consulta detectada como búsqueda nueva, NO es acción de mostrar")
```

**Resultado:** Las búsquedas nuevas ahora se ejecutan normalmente, sin ser interceptadas como acciones de mostrar.

---

### 2. Removida Detección Genérica Demasiado Amplia

**Archivo:** `backend/services/chat_service.py` (línea ~571)

Se removió la detección genérica de "del titulo que" que era demasiado amplia:

**Antes:**
```python
"del titulo que", "del título que"  # ❌ Demasiado genérico
```

**Después:**
```python
# Solo frases específicas como:
"del titulo que encontraste", "del título que encontraste",
"del titulo encontrado", "del título encontrado"
```

**Resultado:** Solo se detectan acciones de mostrar cuando son explícitas y específicas.

---

## 🔄 Flujo Corregido

### Antes (Fallaba):
```
1. Usuario: "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
2. Sistema detecta "con vencimiento" o "valoración" 
3. ❌ Se interpreta erróneamente como acción de mostrar
4. ❌ No se ejecuta la búsqueda
5. ❌ Responde: "No se encontraron valoraciones"
```

### Después (Funciona):
```
1. Usuario: "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
2. Sistema detecta "cuál es" y "valoración de un"
3. ✅ Se identifica como búsqueda nueva
4. ✅ Se ejecuta la búsqueda normalmente
5. ✅ Encuentra y muestra los resultados
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Búsqueda Nueva con Nemotécnico

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
- ✅ SIRIUS detecta que es búsqueda nueva
- ✅ NO se trata como acción de mostrar
- ✅ Ejecuta búsqueda normal
- ✅ Encuentra y muestra resultados

### Escenario 2: Acción de Mostrar (con contexto previo)

**Consulta 1:** "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
- SIRIUS encuentra 1 título
- Contexto guardado

**Consulta 2:** "Muéstrame la información del título que encontraste"
- ✅ SIRIUS detecta "muestrame" y "que encontraste"
- ✅ Es acción de mostrar
- ✅ Muestra resultados del contexto

---

## 📝 Palabras Clave de Búsqueda Nueva

Las siguientes palabras indican que es una búsqueda nueva (NO acción de mostrar):

- "cuál es" / "cual es"
- "cuál es la" / "cual es la"
- "quiero saber"
- "necesito"
- "valoración de un" / "valoracion de un"
- "tir de valoración"
- "precio de"
- "con vencimiento"

---

*Última actualización: 29 de noviembre de 2025*

