# Reversión de Cambios en Búsqueda por Nemotécnico

## Problema
Después de implementar cambios para hacer la búsqueda por nemotécnico más flexible, SIRIUS dejó de encontrar cualquier resultado, mostrando "No se encontraron valoraciones" incluso para consultas que antes funcionaban.

## Cambios Revertidos

### 1. Búsqueda de Nemotécnico
- **Revertido a**: Búsqueda exacta case-insensitive: `ilike.{nemotecnico}`
- **Eliminado**: Búsqueda flexible con comodines `ilike.%{nemotecnico}%`

### 2. Filtro de Nemotécnico en Memoria
- **Eliminado**: El filtro adicional de nemotécnico exacto que se ejecutaba después de procesar el DataFrame
- **Motivo**: Este filtro estaba siendo demasiado estricto y eliminaba todos los resultados

## Estado Actual

SIRIUS ahora está de vuelta a la funcionalidad anterior:
- ✅ Búsqueda exacta case-insensitive por nemotécnico
- ✅ Encuentra resultados (aunque pueda faltar 1 ISIN de los 4 esperados)
- ❌ Sigue sin encontrar el ISIN `COB13CD1K4D3` para la consulta con CDTBGAS0V

## Archivos Modificados

### `backend/services/query_service.py`
- Línea 258: Revertida a búsqueda exacta: `ilike.{nemotecnico}`
- Eliminado el bloque de filtrado de nemotécnico en memoria (líneas 418-464)

## Notas

El problema original (no encontrar el 4to ISIN) persiste, pero ahora SIRIUS al menos encuentra 3 resultados como antes. El problema específico del ISIN faltante `COB13CD1K4D3` requiere un diagnóstico más profundo mediante los logs del servidor para entender:

1. Si el ISIN está en Supabase con ese nemotécnico
2. Si el nemotécnico está almacenado de manera diferente
3. Si el filtro de fecha está eliminando el ISIN

Los cambios anteriores que agregan logging detallado siguen en el código y pueden ayudar a diagnosticar el problema.

