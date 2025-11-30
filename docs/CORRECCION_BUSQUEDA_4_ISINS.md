# 🔧 Corrección: Búsqueda por Nemotécnico Encuentra Solo 2 de 4 ISINs

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** Cuando se busca "CDTBGAS0V con vencimiento del 30/08/2027", SIRIUS encuentra solo 2 títulos cuando debería encontrar 4.

**ISINs esperados:**
- COB13CD02G01
- COB13CD1K3N4
- COB13CD1K4D3
- COB13CD2IIA0

**ISINs encontrados (incorrecto):** Solo 2

---

## 🐛 Problema Identificado

### Búsqueda Incompleta

**Síntoma:**
- Usuario pregunta: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
- SIRIUS encuentra 2 títulos
- **Problema:** Debería encontrar 4 títulos con esos ISINs

**Posibles causas:**
1. Límite de registros demasiado bajo (solo 500)
2. Filtro de fecha de vencimiento eliminando títulos válidos
3. Búsqueda incompleta en uno o ambos proveedores (PIP/Precia)
4. Datos no disponibles en Supabase para todos los ISINs

---

## ✅ Correcciones Implementadas

### 1. Aumentar Límite de Registros

**Archivo:** `backend/services/query_service.py` (línea ~278)

**Cambio:** Aumentar límite de 500 a 1000 cuando hay fecha de vencimiento:

```python
# ANTES:
limit_value = "500" if query.fecha_vencimiento else "100"

# DESPUÉS:
limit_value = "1000" if query.fecha_vencimiento else "100"
```

**Resultado:** Asegura que se obtengan más registros antes de aplicar el filtro de fecha de vencimiento.

---

### 2. Logging Mejorado para Diagnóstico

**Archivo:** `backend/services/query_service.py`

**Cambio:** Agregar logging detallado para identificar qué ISINs se encuentran:

#### A. Log de ISINs por Proveedor

```python
# Log de ISINs únicos encontrados por proveedor
if valuations:
    isins_por_proveedor = set(v.isin for v in valuations if v.isin)
    logger.info(f"📋 ISINs únicos encontrados en {provider.value}: {len(isins_por_proveedor)} → {sorted(isins_por_proveedor)}")
```

#### B. Log de ISINs Antes y Después del Filtro de Fecha

```python
# Log de ISINs después del filtro de fecha
if valuations:
    isins_despues_filtro = set(v.isin for v in valuations if v.isin)
    logger.info(f"📋 ISINs únicos DESPUÉS del filtro de fecha en {provider.value}: {len(isins_despues_filtro)} → {sorted(isins_despues_filtro)}")
```

#### C. Log de Resumen Final

```python
# Log final: mostrar todos los ISINs únicos encontrados después de combinar ambos proveedores
if all_valuations:
    isins_totales = set(v.isin for v in all_valuations if v.isin)
    logger.info(f"📊 RESUMEN FINAL: Total de valoraciones: {len(all_valuations)}, ISINs únicos encontrados: {len(isins_totales)}")
    logger.info(f"📋 ISINs encontrados: {sorted(isins_totales)}")
```

**Resultado:** Facilita el diagnóstico para identificar:
- Qué ISINs se encuentran en cada proveedor
- Qué ISINs se pierden después del filtro de fecha
- Qué ISINs se encuentran en total después de combinar ambos proveedores

---

### 3. Logging Adicional para Fechas de Vencimiento

**Archivo:** `backend/services/query_service.py` (línea ~427)

**Cambio:** Mejorar logging cuando el filtro de fecha no reduce resultados:

```python
if resultados_antes == resultados_despues:
    logger.warning(f"⚠️ Filtro de fecha de vencimiento no redujo resultados...")
    # Log adicional
    if valuations:
        fechas_encontradas = set()
        isins_antes_filtro = set()
        for v in valuations[:20]:  # Revisar primeras 20
            if v.fecha_vencimiento:
                fechas_encontradas.add(str(v.fecha_vencimiento))
            if v.isin:
                isins_antes_filtro.add(v.isin)
        logger.info(f"Fechas de vencimiento encontradas: {sorted(fechas_encontradas)}")
        logger.info(f"ISINs en los primeros resultados: {sorted(isins_antes_filtro)}")
```

**Resultado:** Permite identificar si las fechas de vencimiento están en el formato correcto y qué ISINs tienen esas fechas.

---

## 🔄 Flujo Mejorado

### Proceso de Búsqueda:

```
1. Usuario: "CDTBGAS0V con vencimiento 30/08/2027"
2. Busca en Supabase (PIP) con nemotécnico exacto
   - Límite: 1000 registros
   - Log: ISINs encontrados en PIP
3. Busca en Supabase (Precia) con nemotécnico exacto
   - Límite: 1000 registros
   - Log: ISINs encontrados en Precia
4. Filtra por fecha de vencimiento en cada proveedor
   - Log: ISINs después del filtro por proveedor
5. Combina resultados de ambos proveedores
   - Log: Resumen final con todos los ISINs encontrados
6. ✅ Debe encontrar los 4 ISINs esperados
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Búsqueda Completa

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"

**Resultado esperado:**
- ✅ Encuentra 4 ISINs: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3, COB13CD2IIA0
- ✅ Logs muestran ISINs encontrados en cada proveedor
- ✅ Logs muestran ISINs después del filtro de fecha
- ✅ Log final muestra los 4 ISINs

---

## 📝 Notas Técnicas

### Por qué Aumentar el Límite

Cuando hay fecha de vencimiento, necesitamos obtener más registros iniciales para asegurar que el filtro de fecha de vencimiento tenga suficientes datos para trabajar. Si limitamos a 500 y hay más títulos con el mismo nemotécnico pero diferentes fechas de vencimiento, podríamos perder algunos.

### Diagnóstico con Logs

Los logs mejorados permiten identificar:
1. **En qué proveedor faltan ISINs:** Si se encuentran en PIP pero no en Precia, o viceversa
2. **Si el filtro de fecha está eliminando ISINs:** Comparar ISINs antes y después del filtro
3. **Formato de fechas:** Ver qué formatos de fecha tienen los datos en Supabase

---

## 🔍 Próximos Pasos

Si después de estos cambios aún no se encuentran los 4 ISINs:

1. **Revisar logs** para identificar:
   - ¿En qué proveedor faltan ISINs?
   - ¿El filtro de fecha está eliminando ISINs válidos?
   - ¿Qué formatos de fecha tienen los datos?

2. **Verificar datos en Supabase** para confirmar que los 4 ISINs están disponibles

3. **Ajustar filtro de fecha** si es necesario (permitir rangos pequeños si hay diferencias de formato)

---

*Última actualización: 29 de noviembre de 2025*

