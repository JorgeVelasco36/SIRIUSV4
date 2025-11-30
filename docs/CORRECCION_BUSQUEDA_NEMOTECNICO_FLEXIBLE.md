# Corrección: Búsqueda Flexible por Nemotécnico

## Problema Identificado
SIRIUS no está encontrando el ISIN `COB13CD1K4D3` cuando se busca por nemotécnico `CDTBGAS0V` con fecha de vencimiento `30/08/2027`. El problema es que la búsqueda por nemotécnico es demasiado estricta y no captura variaciones en cómo está almacenado el nemotécnico en las bases de datos.

## Cambios Realizados

### 1. Búsqueda Flexible en Supabase
- **Antes**: Búsqueda exacta case-insensitive: `ilike.{nemotecnico}`
- **Ahora**: Búsqueda flexible con comodines: `ilike.%{nemotecnico}%`
- Esto permite encontrar nemotécnicos aunque tengan espacios, variaciones de mayúsculas/minúsculas, o estén incluidos en otros campos

### 2. Filtro de Nemotécnico Exacto en Memoria
Después de obtener los resultados de Supabase con búsqueda flexible, se agrega un filtro adicional que:
- Normaliza el nemotécnico buscado (mayúsculas y sin espacios)
- Compara con el nemotécnico en los campos `emisor` o `tipo_instrumento` de cada resultado
- Solo incluye resultados que realmente coinciden con el nemotécnico buscado
- Esto asegura que no se incluyan resultados no deseados de la búsqueda flexible

### 3. Logging Mejorado
- Se agregó logging para el filtro de nemotécnico
- Se verifica si el ISIN faltante está presente después del filtro de nemotécnico
- Se muestran los nemotécnicos encontrados para debugging

## Flujo de Búsqueda

1. **Búsqueda en Supabase (flexible)**: 
   - Para cada proveedor (PIP y Precia), se hace una búsqueda con `ilike.%{nemotecnico}%`
   - Esto trae todos los registros que contienen el nemotécnico, incluso con variaciones

2. **Procesamiento del DataFrame**:
   - Los datos se normalizan y se convierten en objetos `Valuation`

3. **Filtro de Nemotécnico Exacto**:
   - Se filtran los resultados para incluir solo aquellos que realmente coinciden con el nemotécnico buscado
   - Se busca en los campos `emisor` y `tipo_instrumento`

4. **Filtro de Fecha de Vencimiento**:
   - Se aplica el filtro de fecha de vencimiento exacta

5. **Agrupación de Resultados**:
   - Los resultados de ambos proveedores se combinan en `all_valuations`

## Archivos Modificados

### `backend/services/query_service.py`
- **Línea 265**: Cambio de búsqueda exacta a flexible: `ilike.%{nemotecnico}%`
- **Líneas 418-467**: Agregado filtro de nemotécnico exacto después de procesar el DataFrame
- Agregado logging detallado para rastrear el proceso de filtrado

## Comportamiento Esperado

Después de estos cambios, SIRIUS debería:
- ✅ Encontrar nemotécnicos aunque tengan variaciones en espacios o mayúsculas/minúsculas
- ✅ Capturar todos los ISINs que realmente corresponden al nemotécnico buscado
- ✅ Excluir resultados no deseados que puedan venir de la búsqueda flexible
- ✅ Incluir el ISIN `COB13CD1K4D3` si está en la base de datos con el nemotécnico correcto

## Próximos Pasos

1. Ejecutar la consulta nuevamente: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
2. Revisar los logs para ver:
   - Cuántos resultados se obtienen de Supabase con la búsqueda flexible
   - Cuántos resultados quedan después del filtro de nemotécnico exacto
   - Si el ISIN `COB13CD1K4D3` está presente en cada etapa
3. Si aún no se encuentra el ISIN, los logs mostrarán los nemotécnicos encontrados para ayudar a diagnosticar el problema

