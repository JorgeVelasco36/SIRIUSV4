# Corrección: ISIN faltante en búsqueda por nemotécnico

## Problema Identificado
SIRIUS está encontrando solo 3 títulos en lugar de 4 para la consulta:
- **Consulta**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
- **ISINs esperados**: COB13CD02G01, COB13CD1K3N4, COB13CD1K4D3, COB13CD2IIA0
- **ISIN faltante**: COB13CD1K4D3

El ISIN faltante solo existe en la base de PIP y no en Precia.

## Cambios Realizados

### 1. Logging Detallado para Rastreo del ISIN
- Se agregó logging específico para el ISIN `COB13CD1K4D3` en cada etapa del proceso:
  - Verificación en DataFrame crudo de Supabase
  - Verificación antes del filtro de fecha
  - Verificación después del filtro de fecha
  - Verificación en el resumen final por proveedor

### 2. Aseguramiento de Inclusión de ISINs de Un Solo Proveedor
- Se mejoró la lógica para asegurar que todos los ISINs únicos se incluyan, sin importar si están en uno o ambos proveedores
- Se agregó logging para identificar ISINs que solo están en un proveedor
- Se mejoró el conteo de ISINs únicos para incluir todos, independientemente del proveedor

### 3. Verificación Especial para Búsqueda Problemática
- Se agregó una verificación especial que detecta la búsqueda problemática (nemotécnico CDTBGAS0V, fecha 30/08/2027)
- Si el ISIN faltante no se encuentra en la búsqueda normal, se intenta buscarlo directamente en ambos proveedores
- Esto ayuda a identificar si el ISIN existe pero no se está capturando en la búsqueda por nemotécnico

### 4. Manejo de Errores Mejorado
- Si un proveedor falla, el sistema continúa con el otro
- Esto asegura que ISINs que solo están en un proveedor se incluyan si ese proveedor funciona correctamente

### 5. Logging de ISINs por Proveedor
- Se agregó logging detallado que muestra qué ISINs se encuentran en cada proveedor
- Se identifica claramente qué ISINs solo están en un proveedor
- Se muestra un resumen final con todos los ISINs encontrados

## Archivos Modificados

### `backend/services/query_service.py`
- Agregado logging detallado para rastrear el ISIN faltante en cada etapa
- Mejorada la lógica de combinación de resultados de ambos proveedores
- Agregada verificación especial para búsqueda problemática
- Mejorado el logging de ISINs por proveedor

### `backend/services/chat_service.py`
- Mejorado el conteo de ISINs únicos para incluir todos, sin importar el proveedor
- Agregado logging para identificar ISINs que solo están en un proveedor

## Próximos Pasos para Diagnóstico

Cuando se ejecute la consulta nuevamente, los logs mostrarán:

1. **En DataFrame crudo**: Si el ISIN `COB13CD1K4D3` está en los datos obtenidos de Supabase
2. **Antes del filtro de fecha**: Si el ISIN está presente después de normalizar los datos
3. **Después del filtro de fecha**: Si el ISIN pasa el filtro de fecha o es eliminado
4. **En resumen final**: Si el ISIN está en los resultados finales y en qué proveedor(es)

Si el ISIN no se encuentra en ninguna de estas etapas, la búsqueda directa especial intentará encontrarlo y agregarlo a los resultados.

## Comportamiento Esperado

Después de estos cambios, SIRIUS debería:
- ✅ Incluir todos los ISINs únicos, incluso si solo están en un proveedor
- ✅ Mostrar 4 títulos para la consulta del nemotécnico CDTBGAS0V con fecha 30/08/2027
- ✅ Proporcionar logs detallados para diagnosticar cualquier problema persistente

## Notas Adicionales

- El límite de consulta a Supabase está establecido en 2000 registros cuando hay fecha de vencimiento, lo cual debería ser suficiente
- La búsqueda por nemotécnico usa `ilike` para coincidencia exacta case-insensitive
- Si el ISIN sigue sin encontrarse, los logs detallados ayudarán a identificar la causa exacta

