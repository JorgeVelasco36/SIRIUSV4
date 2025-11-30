# 🔧 Corrección: Búsqueda Incremental Solo Encuentra 2 de 4 Títulos

**Fecha:** 30 de noviembre de 2025  
**Problema:** SIRIUS solo encuentra 2 títulos cuando debería encontrar 4 para la consulta por nemotécnico y fecha de vencimiento.

---

## 📋 Problema Reportado

**Consulta del usuario:**
```
¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?
```

**Comportamiento actual:**
- SIRIUS responde: "Se encontraron 2 títulos que coinciden con tu búsqueda."

**Comportamiento esperado:**
- Debería encontrar 4 títulos con las características:
  1. COB13CD02G01 - Tasa Facial: 7,5817%
  2. COB13CD1K3N4 - Tasa Facial: 14,2232%
  3. COB13CD1K4D3 - Tasa Facial: 15,5200%
  4. COB13CD2IIA0 - Tasa Facial: 9,1325%

Todos tienen:
- Nemotécnico: CDTBGAS0V
- Fecha de Vencimiento: 30/08/2027

---

## 🔍 Análisis del Problema

### Posibles Causas

1. **La búsqueda incremental no está obteniendo todos los resultados de Supabase**
   - Puede estar limitando los resultados en algún paso
   - Puede estar filtrando incorrectamente antes de obtener todos los datos

2. **El filtro de fecha de vencimiento está siendo demasiado estricto**
   - Aunque tiene tolerancia de ±1 día, puede estar perdiendo algunos títulos

3. **Los resultados no se están combinando correctamente entre proveedores**
   - Puede haber un problema al combinar resultados de PIP y Precia

4. **La consulta inicial no está incluyendo la fecha de vencimiento correctamente**
   - Cuando hay nemotécnico + fecha, puede que no se estén obteniendo todos los resultados

---

## ✅ Correcciones Implementadas

### 1. Incluir Fecha de Vencimiento Desde el Inicio

**Ubicación:** `backend/services/chat_service.py` (línea ~1574)

**Cambio:**
- La búsqueda incremental ahora incluye la fecha de vencimiento desde el paso 1 cuando hay nemotécnico
- Esto asegura que se obtengan todos los resultados correctos desde el inicio

**Código:**
```python
query_nemotecnico = ValuationQuery(
    emisor=query.emisor,
    tipo_instrumento=query.tipo_instrumento,
    proveedor=query.proveedor,
    fecha=query.fecha,
    fecha_vencimiento=query.fecha_vencimiento  # Incluir desde el inicio
)
```

### 2. Logging Mejorado para Rastrear ISINs

**Ubicación:** `backend/services/chat_service.py` (línea ~1590)

**Cambio:**
- Se agregó logging detallado para rastrear cuántos ISINs únicos se encuentran en cada paso
- Esto ayuda a identificar dónde se están perdiendo los títulos

**Código:**
```python
# Contar ISINs únicos encontrados
isins_unicos = set()
for v in resultados_intermedios:
    isin = self._get_valuation_field(v, "isin")
    if isin:
        isins_unicos.add(isin)
logger.info(f"   📋 ISINs únicos encontrados después del paso 1: {len(isins_unicos)} → {sorted(isins_unicos)}")
```

### 3. Log Final de Resumen

**Ubicación:** `backend/services/chat_service.py` (línea ~1665)

**Cambio:**
- Se agregó un log final que muestra todos los ISINs únicos encontrados después de la búsqueda incremental
- Esto ayuda a verificar que se están obteniendo todos los resultados esperados

---

## 🧪 Pruebas a Realizar

### Prueba 1: Verificar que Encuentra los 4 Títulos

**Consulta:**
```
¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?
```

**Resultado esperado:**
- Debe encontrar 4 títulos (ISINs únicos)
- Los logs deben mostrar los 4 ISINs: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3, COB13CD2IIA0

### Prueba 2: Verificar Logging

**Verificar en los logs:**
1. ISINs encontrados después del paso 1 (nemotécnico + fecha de vencimiento)
2. ISINs encontrados después de todos los filtros
3. Resumen final de ISINs únicos

### Prueba 3: Verificar Combinación de Proveedores

**Verificar:**
- Que se estén obteniendo resultados de ambos proveedores (PIP y Precia)
- Que se estén combinando correctamente
- Que no se estén duplicando o perdiendo resultados

---

## 📝 Archivos Modificados

1. **`backend/services/chat_service.py`**:
   - Incluir fecha de vencimiento desde el paso 1 de búsqueda incremental
   - Agregar logging detallado de ISINs en cada paso
   - Agregar log final de resumen

---

## 🔄 Próximos Pasos

1. **Ejecutar la consulta de prueba** y revisar los logs
2. **Verificar cuántos ISINs se encuentran** en cada paso
3. **Identificar dónde se están perdiendo** los 2 ISINs faltantes
4. **Ajustar la lógica** según los hallazgos

---

*Última actualización: 30 de noviembre de 2025*

