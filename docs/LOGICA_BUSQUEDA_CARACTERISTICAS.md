# Lógica de Búsqueda por Características

## Flujo Simplificado

La búsqueda por características funciona de la siguiente manera:

### 1. Búsqueda en cada tabla por separado

Para cada proveedor (PIP y Precia):

1. **Buscar por nemotécnico** en la tabla:
   - Ejemplo: Buscar "CDTBGAS0V" en tabla PIP
   - Ejemplo: Buscar "CDTBGAS0V" en tabla Precia

2. **Filtrar por fecha de vencimiento** en los resultados obtenidos:
   - Ejemplo: De los resultados de PIP, filtrar por fecha "30/08/2027"
   - Ejemplo: De los resultados de Precia, filtrar por fecha "30/08/2027"

### 2. Resultados esperados por proveedor

- **PIP**: 4 ISINs únicos después del filtro de fecha
- **Precia**: 3 ISINs únicos después del filtro de fecha

### 3. Combinación de resultados

- Se combinan TODOS los resultados de ambos proveedores
- Se cuentan los **ISINs únicos** del conjunto combinado
- **Resultado final**: 4 títulos únicos
  - 3 ISINs están en ambas tablas (PIP y Precia)
  - 1 ISIN solo está en PIP

## Implementación en el Código

### Archivo: `backend/services/query_service.py`

La función `_query_supabase_directly` implementa esta lógica:

```python
# 1. Para cada proveedor (PIP y Precia)
for provider in [Provider.PIP_LATAM, Provider.PRECIA]:
    # 2. Buscar por nemotécnico en Supabase
    search_params[nemotecnico_col] = f"ilike.{nemotecnico}"
    
    # 3. Obtener todos los registros que coinciden con el nemotécnico
    response = supabase._make_request("GET", table_name, params=params)
    
    # 4. Procesar los datos en objetos Valuation
    valuations = ingestion_service.process_dataframe(df_normalized, ...)
    
    # 5. Filtrar por fecha de vencimiento en memoria
    if query.fecha_vencimiento:
        valuations_filtradas = filtrar_por_fecha(valuations, fecha_vencimiento)
    
    # 6. Agregar resultados al conjunto total
    all_valuations.extend(valuations_filtradas)

# 7. Calcular ISINs únicos del conjunto combinado
isins_totales = set(v.isin for v in all_valuations if v.isin)
```

## Logging para Diagnóstico

El código incluye logging detallado en cada paso:

1. **Logs por proveedor**: Muestra cuántos ISINs únicos se encuentran en cada tabla
2. **Log antes del filtro de fecha**: Muestra todos los ISINs encontrados por nemotécnico
3. **Log después del filtro de fecha**: Muestra los ISINs que pasaron el filtro
4. **Log final**: Muestra el total de ISINs únicos después de combinar ambas tablas
5. **Log de ISINs por proveedor**: Identifica qué ISINs están en cada proveedor

## Validación

Para validar que la lógica funciona correctamente:

1. **Ejecutar la consulta**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"

2. **Revisar los logs**:
   - ¿Se encuentran 4 ISINs en PIP?
   - ¿Se encuentran 3 ISINs en Precia?
   - ¿El resultado final muestra 4 ISINs únicos?
   - ¿El ISIN faltante `COB13CD1K4D3` está en los logs de PIP?

3. **Si no se encuentra el ISIN faltante**, los logs mostrarán:
   - Si el ISIN está en el DataFrame crudo de Supabase
   - Si se elimina por el filtro de fecha
   - En qué etapa se pierde el ISIN

