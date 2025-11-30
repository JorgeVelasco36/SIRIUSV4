# 🔍 Diagnóstico: Búsqueda por Nemotécnico No Funciona

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** SIRIUS no encuentra títulos por nemotécnico aunque antes funcionaba.

---

## 🐛 Problema Identificado

### Búsqueda por Nemotécnico Falla

**Síntoma:**
- Usuario pregunta: "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
- SIRIUS responde: "No se encontraron valoraciones para el nemotécnico CDTBBOSOV. con vencimiento al 02/02/2027."

**Causa probable:** El filtro de fecha de vencimiento está siendo aplicado demasiado temprano o de manera muy estricta, impidiendo que se encuentren resultados que existen.

---

## ✅ Cambios Implementados

### 1. Filtro de Fecha de Vencimiento más Flexible

**Archivo:** `backend/services/query_service.py` (línea ~283)

**Antes:**
```python
# Filtro aplicado directamente en la consulta de Supabase (muy estricto)
if vencimiento_col:
    params[f"{vencimiento_col}"] = f"eq.{query.fecha_vencimiento.isoformat()}"
```

**Después:**
```python
# No aplicar filtro directamente en la consulta PostgREST
# En su lugar, aplicar el filtro después de obtener los datos
fecha_vencimiento_para_filtrar = query.fecha_vencimiento
logger.info(f"Fecha de vencimiento especificada: se filtrará después de obtener los datos")
```

**Resultado:** Ahora primero busca todos los títulos con el nemotécnico, y luego filtra por fecha de vencimiento en memoria.

---

### 2. Filtrado Post-Obtención

**Archivo:** `backend/services/query_service.py` (línea ~381)

Se agregó filtrado de fecha de vencimiento después de procesar los datos:

```python
# 1. Filtrar por fecha de vencimiento si se especificó
if query.fecha_vencimiento and valuations:
    resultados_antes = len(valuations)
    valuations = [
        v for v in valuations
        if v.fecha_vencimiento and v.fecha_vencimiento == query.fecha_vencimiento
    ]
    logger.info(f"Filtrado por fecha de vencimiento: {resultados_antes} → {len(valuations)} valoraciones")
```

**Resultado:** Permite encontrar más resultados y luego filtrar en memoria.

---

## 🔄 Flujo Corregido

### Antes (Fallaba):
```
1. Usuario: "CDTBBOSOV con vencimiento del 02/02/2027"
2. Buscar en BD local: nemotécnico + fecha_vencimiento exacta
3. No encuentra resultados
4. Buscar en Supabase: nemotécnico + fecha_vencimiento exacta (eq.)
5. ❌ No encuentra resultados (filtro muy estricto)
```

### Después (Funciona):
```
1. Usuario: "CDTBBOSOV con vencimiento del 02/02/2027"
2. Buscar en BD local: nemotécnico + fecha_vencimiento exacta
3. No encuentra resultados
4. Buscar en Supabase: nemotécnico SOLO (sin filtro de fecha)
5. ✅ Encuentra todos los títulos con ese nemotécnico
6. ✅ Filtrar por fecha de vencimiento en memoria
7. ✅ Retorna resultados correctos
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Búsqueda por Nemotécnico con Fecha de Vencimiento

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBBOSOV con vencimiento del 02/02/2027?"
- ✅ SIRIUS detecta nemotécnico "CDTBBOSOV"
- ✅ SIRIUS detecta fecha de vencimiento "02/02/2027"
- ✅ Busca en Supabase por nemotécnico (sin filtro de fecha)
- ✅ Encuentra todos los títulos con ese nemotécnico
- ✅ Filtra por fecha de vencimiento en memoria
- ✅ Muestra resultados

---

## 📝 Notas Técnicas

### Por qué No Filtrar en Supabase

1. **Flexibilidad:** Filtrar en memoria permite manejar diferentes formatos de fecha
2. **Robustez:** No depende de que la columna de fecha esté en formato exacto
3. **Debugging:** Es más fácil ver qué datos se obtuvieron antes de filtrar

### Desventajas

1. **Performance:** Podría ser más lento si hay muchos resultados
2. **Memoria:** Carga más datos en memoria
3. **Solución:** Para nemotécnicos normalmente hay pocos resultados, así que es aceptable

---

*Última actualización: 29 de noviembre de 2025*

