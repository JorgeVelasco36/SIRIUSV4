# Corrección: Paginación Completa para Obtener Todos los Registros

## Problema Identificado
SIRIUS solo encuentra 3 títulos en lugar de 4 para la consulta con nemotécnico `CDTBGAS0V` y fecha de vencimiento `30/08/2027`. El problema puede estar relacionado con límites en las consultas a Supabase que impiden obtener todos los registros disponibles.

## Cambios Realizados

### 1. Eliminación del Límite de 2000
- **Antes**: Límite de 2000 registros para búsquedas con fecha de vencimiento
- **Ahora**: Límite inicial de 5000 registros + paginación para obtener TODOS los registros

### 2. Implementación de Paginación Completa
- **Nuevo**: Sistema de paginación que obtiene TODOS los registros disponibles
- **Mecanismo**:
  1. Obtiene el primer lote de hasta 5000 registros
  2. Si hay más registros, continúa obteniendo en lotes de 5000
  3. Continúa hasta que no haya más registros disponibles
  4. Combina todos los registros en un solo DataFrame

### 3. Logging Mejorado
- Muestra cuántos registros se obtienen en cada página
- Muestra el total acumulado de registros
- Indica cuando se han obtenido TODOS los registros disponibles

## Implementación Técnica

### Flujo de Paginación

```python
# Para cada proveedor (PIP y Precia)
for provider in [Provider.PIP_LATAM, Provider.PRECIA]:
    all_records = []
    offset = 0
    limit_per_page = 5000
    
    while iteration < max_iterations:
        # Obtener página de resultados
        page_params = params.copy()
        page_params["offset"] = str(offset)
        page_params["limit"] = str(limit_per_page)
        
        response = supabase._make_request("GET", table_name, params=page_params)
        
        # Agregar registros al total
        all_records.extend(response)
        
        # Si obtuvimos menos que el límite, ya tenemos todos
        if len(response) < limit_per_page:
            break
        
        # Continuar con la siguiente página
        offset += limit_per_page
        iteration += 1
    
    # Procesar TODOS los registros obtenidos
    df = pd.DataFrame(all_records)
```

### Ventajas

1. **Obtiene TODOS los registros**: No se pierde ningún registro por límites
2. **Eficiente**: Obtiene en lotes grandes (5000) para minimizar el número de peticiones
3. **Seguro**: Tiene un límite máximo de iteraciones para prevenir loops infinitos
4. **Transparente**: Logging detallado de cada paso

## Archivos Modificados

### `backend/services/query_service.py`
- **Líneas 269-280**: Configuración inicial con límite de 5000
- **Líneas 317-358**: Implementación de paginación completa
- Agregado logging detallado para rastrear la obtención de registros

## Comportamiento Esperado

Después de estos cambios, SIRIUS debería:
- ✅ Obtener TODOS los registros que coinciden con el nemotécnico de cada tabla
- ✅ No perder ningún ISIN por límites de consulta
- ✅ Procesar todos los registros antes de filtrar por fecha de vencimiento
- ✅ Encontrar los 4 ISINs esperados:
  - COB13CD02G01 (en PIP y Precia)
  - COB13CD1K3N4 (en PIP y Precia)
  - COB13CD1K4D3 (solo en PIP) ← Este es el que faltaba
  - COB13CD2IIA0 (en PIP y Precia)

## Próximos Pasos

1. **Ejecutar la consulta nuevamente**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"

2. **Revisar los logs** para verificar:
   - Cuántos registros se obtienen de cada tabla en total
   - Si la paginación está funcionando correctamente
   - Si el ISIN `COB13CD1K4D3` está presente en los registros obtenidos

3. **Si el problema persiste**, los logs mostrarán:
   - Si el ISIN está en los registros obtenidos de Supabase
   - Si se elimina por el filtro de fecha de vencimiento
   - En qué etapa exacta se pierde el ISIN

## Notas Técnicas

- PostgREST (API de Supabase) permite paginación usando parámetros `offset` y `limit`
- El límite máximo por defecto de PostgREST puede ser 1000, pero usando paginación podemos obtener más
- El sistema ahora obtiene registros en lotes de 5000 hasta agotar todos los disponibles
- La paginación se detiene cuando se reciben menos registros que el límite solicitado

