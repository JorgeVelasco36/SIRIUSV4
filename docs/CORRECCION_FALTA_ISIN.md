# 🔧 Corrección: Falta ISIN COB13CD1K4D3 en Búsqueda

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** Cuando se busca "CDTBGAS0V con vencimiento del 30/08/2027", SIRIUS encuentra solo 3 títulos cuando debería encontrar 4.

**ISINs esperados:**
- ✅ COB13CD02G01 (encontrado)
- ✅ COB13CD1K3N4 (encontrado)
- ✅ COB13CD2IIA0 (encontrado)
- ❌ COB13CD1K4D3 (falta)

---

## 🐛 Problema Identificado

### Búsqueda Incompleta - Falta 1 ISIN

**Síntoma:**
- Usuario pregunta: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
- SIRIUS encuentra 3 títulos
- **Problema:** Debería encontrar 4 títulos, falta COB13CD1K4D3

**Posibles causas:**
1. Límite de registros demasiado bajo (solo 1000)
2. Parseo de fechas insuficiente (no reconoce todos los formatos)
3. El ISIN no está en Supabase para ese nemotécnico y fecha
4. Filtro de fecha de vencimiento eliminando el ISIN

---

## ✅ Correcciones Implementadas

### 1. Aumentar Límite de Registros a 2000

**Archivo:** `backend/services/query_service.py` (línea ~279)

**Cambio:** Aumentar límite de 1000 a 2000:

```python
# ANTES:
limit_value = "1000" if query.fecha_vencimiento else "100"

# DESPUÉS:
limit_value = "2000" if query.fecha_vencimiento else "100"
```

**Resultado:** Asegura que se obtengan aún más registros antes de aplicar el filtro de fecha de vencimiento.

---

### 2. Mejorar Parseo de Fechas de Vencimiento

**Archivo:** `backend/services/query_service.py` (línea ~417)

**Cambio:** Mejorar el parseo de fechas para manejar múltiples formatos:

```python
# ANTES: Solo intentaba fromisoformat
if isinstance(fecha_v, str):
    fecha_v = datetime.fromisoformat(fecha_v).date()

# DESPUÉS: Intenta múltiples formatos
if isinstance(fecha_v, str):
    try:
        fecha_v = datetime.fromisoformat(fecha_v).date()
    except:
        try:
            # Formato DD/MM/YYYY o DD-MM-YYYY
            import re
            match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', fecha_v)
            if match:
                dia, mes, año = match.groups()
                fecha_v = date(int(año), int(mes), int(dia))
            else:
                # Intentar parsear con pandas
                fecha_v = pd.to_datetime(fecha_v).date()
        except:
            logger.warning(f"No se pudo parsear fecha de vencimiento: {fecha_v}")
            continue
```

**Resultado:** Asegura que las fechas se parseen correctamente independientemente del formato en Supabase.

---

### 3. Mejorar Logging de ISINs Antes del Filtro

**Archivo:** `backend/services/query_service.py` (línea ~399)

**Cambio:** Mostrar todos los ISINs encontrados antes del filtro:

```python
# ANTES:
logger.info(f"ISINs únicos encontrados antes de filtrar: {len(isins_unicos)} (muestra: {list(isins_unicos)[:5]})")

# DESPUÉS:
logger.info(f"📋 ISINs únicos encontrados en {provider.value} ANTES de filtrar por fecha: {len(isins_unicos)} → {sorted(isins_unicos)}")
```

**Resultado:** Facilita identificar qué ISINs se pierden después del filtro de fecha.

---

## 🔄 Flujo Mejorado

### Proceso de Búsqueda:

```
1. Usuario: "CDTBGAS0V con vencimiento 30/08/2027"
2. Busca en Supabase (PIP) con nemotécnico exacto
   - Límite: 2000 registros
   - Log: ISINs encontrados en PIP ANTES del filtro
3. Busca en Supabase (Precia) con nemotécnico exacto
   - Límite: 2000 registros
   - Log: ISINs encontrados en Precia ANTES del filtro
4. Filtra por fecha de vencimiento en cada proveedor
   - Parseo mejorado de fechas (múltiples formatos)
   - Log: ISINs después del filtro por proveedor
5. Combina resultados de ambos proveedores
   - Log: Resumen final con todos los ISINs encontrados
6. ✅ Debe encontrar los 4 ISINs esperados (incluyendo COB13CD1K4D3)
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Búsqueda Completa - 4 ISINs

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"

**Resultado esperado:**
- ✅ Encuentra 4 ISINs: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3, COB13CD2IIA0
- ✅ Logs muestran ISINs encontrados en cada proveedor ANTES del filtro
- ✅ Logs muestran ISINs después del filtro de fecha
- ✅ Log final muestra los 4 ISINs

---

## 📝 Notas Técnicas

### Por qué Aumentar el Límite a 2000

Si hay muchos títulos con el mismo nemotécnico pero diferentes fechas de vencimiento, o si algunos títulos tienen múltiples valoraciones (por proveedor), necesitamos obtener más registros para asegurar que no perdamos ningún ISIN válido.

### Por qué Mejorar el Parseo de Fechas

Los datos en Supabase pueden tener fechas en diferentes formatos:
- ISO format: "2027-08-30"
- DD/MM/YYYY: "30/08/2027"
- DD-MM-YYYY: "30-08-2027"
- Timestamp: "2027-08-30T00:00:00"

El parseo mejorado intenta múltiples formatos para asegurar que todas las fechas se comparen correctamente.

---

## 🔍 Diagnóstico

Si después de estos cambios aún falta el ISIN COB13CD1K4D3, los logs mostrarán:

1. **¿El ISIN está en Supabase?**
   - Revisar logs de ISINs ANTES del filtro
   - Si aparece en los logs, el problema es el filtro de fecha
   - Si no aparece, el problema es la búsqueda inicial

2. **¿El filtro de fecha lo está eliminando?**
   - Comparar logs ANTES y DESPUÉS del filtro
   - Si desaparece después del filtro, revisar el formato de fecha de ese ISIN

3. **¿El ISIN está en ambos proveedores?**
   - Revisar logs por proveedor
   - Si solo está en un proveedor, verificar que se esté consultando ambos

---

*Última actualización: 29 de noviembre de 2025*

