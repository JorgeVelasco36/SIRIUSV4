# 🔧 Corrección: Búsqueda por Nemotécnico con Fecha de Vencimiento

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** Cuando se busca por nemotécnico con fecha de vencimiento, SIRIUS encuentra demasiados resultados (ej: 200 títulos cuando solo hay 4).

---

## 🐛 Problema Identificado

### Búsqueda Demasiado Amplia

**Síntoma:**
- Usuario pregunta: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento el 30/08/2027?"
- SIRIUS encuentra 200 títulos
- **Problema:** Solo debería haber 4 títulos con esas características

**Causas identificadas:**
1. La búsqueda por nemotécnico usaba `ilike.%{nemotecnico}%` que permite coincidencias parciales
2. El límite de 100 registros puede estar limitando los resultados antes de aplicar el filtro de fecha de vencimiento
3. El filtro de fecha de vencimiento puede no estar aplicándose correctamente

---

## ✅ Correcciones Implementadas

### 1. Búsqueda Más Estricta por Nemotécnico

**Archivo:** `backend/services/query_service.py` (línea ~260)

**Cambio:** Cambiar de búsqueda parcial a coincidencia exacta:

```python
# ANTES (demasiado amplio):
search_params[f"{nemotecnico_col}"] = f"ilike.%{nemotecnico}%"

# DESPUÉS (más estricto):
search_params[f"{nemotecnico_col}"] = f"ilike.{nemotecnico}"
```

**Resultado:** Ahora busca coincidencia exacta (case-insensitive) en lugar de coincidencias parciales.

---

### 2. Aumentar Límite de Registros cuando hay Fecha de Vencimiento

**Archivo:** `backend/services/query_service.py` (línea ~276)

**Cambio:** Aumentar el límite de registros cuando se especifica fecha de vencimiento:

```python
# Aumentar límite para nemotécnicos con fecha de vencimiento
limit_value = "500" if query.fecha_vencimiento else "100"
params = {
    "select": "*",
    "limit": limit_value
}
```

**Resultado:** Asegura que se obtengan todos los resultados relevantes antes de aplicar el filtro de fecha de vencimiento.

---

### 3. Mejorar Filtro de Fecha de Vencimiento

**Archivo:** `backend/services/query_service.py` (línea ~388)

**Cambio:** Mejorar la comparación de fechas para asegurar que se filtren correctamente:

```python
# Asegurar que ambas fechas sean del mismo tipo para comparar
fecha_vencimiento_buscada = query.fecha_vencimiento
if isinstance(fecha_vencimiento_buscada, str):
    fecha_vencimiento_buscada = datetime.fromisoformat(fecha_vencimiento_buscada).date()

for v in valuations:
    if v.fecha_vencimiento:
        fecha_v = v.fecha_vencimiento
        if isinstance(fecha_v, str):
            fecha_v = datetime.fromisoformat(fecha_v).date()
        elif hasattr(fecha_v, 'date'):
            fecha_v = fecha_v.date()
        
        if fecha_v == fecha_vencimiento_buscada:
            valuations_filtradas.append(v)
```

**Resultado:** Asegura que el filtro de fecha de vencimiento se aplique correctamente, comparando fechas del mismo tipo.

---

### 4. Logging Mejorado para Diagnóstico

**Archivo:** `backend/services/query_service.py`

**Cambio:** Agregar logging adicional para diagnosticar problemas:

```python
# Log de ISINs únicos antes de filtrar
isins_unicos = set(v.isin for v in valuations if v.isin)
logger.info(f"ISINs únicos encontrados antes de filtrar por fecha de vencimiento: {len(isins_unicos)}")

# Log de fechas encontradas si el filtro no reduce resultados
if resultados_antes == resultados_despues:
    fechas_encontradas = set()
    for v in valuations[:10]:
        if v.fecha_vencimiento:
            fechas_encontradas.add(str(v.fecha_vencimiento))
    logger.info(f"Fechas de vencimiento encontradas: {sorted(fechas_encontradas)}")
```

**Resultado:** Facilita el diagnóstico cuando hay problemas con el filtrado.

---

## 🔄 Flujo Corregido

### Antes (Encontraba 200 títulos):
```
1. Usuario: "CDTBGAS0V con vencimiento 30/08/2027"
2. Busca en Supabase con ilike.%CDTBGAS0V% (coincidencias parciales)
3. Encuentra muchos registros que contienen "CDTBGAS0V"
4. Limita a 100 registros
5. Filtra por fecha de vencimiento
6. ❌ Muestra 200 títulos (incorrecto)
```

### Después (Encuentra 4 títulos):
```
1. Usuario: "CDTBGAS0V con vencimiento 30/08/2027"
2. Busca en Supabase con ilike.CDTBGAS0V (coincidencia exacta)
3. Encuentra solo registros con nemotécnico exacto
4. Limita a 500 registros (más espacio para filtrar)
5. Filtra por fecha de vencimiento exacta
6. ✅ Muestra 4 títulos (correcto)
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Nemotécnico con Fecha de Vencimiento

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento el 30/08/2027?"
- ✅ SIRIUS busca nemotécnico exacto (no parcial)
- ✅ Obtiene hasta 500 registros para tener espacio para filtrar
- ✅ Filtra por fecha de vencimiento exacta
- ✅ Muestra solo los 4 títulos correctos

**Resultado esperado:** 4 títulos (no 200)

---

## 📝 Notas Técnicas

### Por qué Coincidencia Exacta

La búsqueda con `ilike.%{nemotecnico}%` puede encontrar:
- "CDTBGAS0V" (correcto)
- "CDTBGAS0V123" (incorrecto - nemotécnico diferente)
- "ABCDTBGAS0V" (incorrecto - nemotécnico diferente)

Usar `ilike.{nemotecnico}` busca solo coincidencias exactas, evitando falsos positivos.

### Por qué Aumentar el Límite

Cuando hay fecha de vencimiento, necesitamos obtener más registros iniciales para asegurar que el filtro de fecha de vencimiento tenga suficientes datos para trabajar. Si limitamos a 100 y hay 200 registros con el nemotécnico, podríamos perder algunos que sí cumplen con la fecha de vencimiento.

---

*Última actualización: 29 de noviembre de 2025*

