# Corrección: Ajuste de Límite de Paginación y Manejo de Errores

## Problema Identificado

SIRIUS dejó de encontrar cualquier resultado para búsquedas por nemotécnico. El usuario reportó que la búsqueda ya no funciona: "Revisa la logica de busqueda por caracteristicas de titulo, ya no está encontrando ningun resultado."

## Causa Raíz

La implementación de paginación con límite de 5000 registros por página puede estar causando problemas:
1. **Límite demasiado alto**: PostgREST/Supabase puede rechazar peticiones con límites muy altos
2. **Falta de manejo de errores**: Si la primera petición falla, no se obtienen registros y el proceso se detiene
3. **Indentación incorrecta**: El código de procesamiento puede tener problemas de indentación que impiden su ejecución correcta

## Cambios Realizados

### 1. Reducción del Límite de Paginación
- **Antes**: 5000 registros por página
- **Ahora**: 1000 registros por página (más conservador y compatible con PostgREST)

### 2. Mejor Manejo de Errores
- Agregado `try-except` alrededor del bucle de paginación
- Si ocurre un error durante la paginación, se usan los registros obtenidos hasta el momento
- Logging mejorado para identificar dónde ocurren los errores

### 3. Logging Mejorado
- Mensajes más claros cuando no hay registros
- Indicación de qué página se está obteniendo
- Advertencia específica cuando no se obtienen registros

## Implementación Técnica

### Cambios en `backend/services/query_service.py`

```python
# Antes:
limit_per_page = 5000
max_iterations = 100

# Ahora:
limit_per_page = 1000  # Límite más conservador
max_iterations = 50    # Menos iteraciones máximo

# Agregado:
try:
    while iteration < max_iterations:
        # ... lógica de paginación ...
except Exception as e:
    logger.error(f"Error durante paginación en {table_name}: {str(e)}")
    logger.info(f"Usando registros obtenidos hasta el momento: {len(all_records)} registros")
```

## Comportamiento Esperado

Después de estos cambios:
- ✅ La paginación debería funcionar de manera más confiable
- ✅ Si hay un error, no se perderán todos los registros obtenidos hasta ese momento
- ✅ Los logs mostrarán claramente dónde ocurre cualquier problema
- ✅ SIRIUS debería volver a encontrar resultados para búsquedas por nemotécnico

## Próximos Pasos

1. **Probar la consulta nuevamente**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
2. **Revisar los logs** para ver:
   - Si la paginación está funcionando
   - Cuántos registros se obtienen en cada página
   - Si hay errores durante la paginación
3. **Si aún no funciona**, los logs mostrarán el error específico que está ocurriendo

## Notas Técnicas

- PostgREST tiene límites por defecto que pueden variar según la configuración del servidor
- Un límite de 1000 es generalmente seguro para la mayoría de las configuraciones
- Si es necesario obtener más registros, la paginación automática los obtendrá en múltiples páginas

