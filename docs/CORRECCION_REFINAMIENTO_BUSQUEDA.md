# Corrección: Mejora en la Lógica de Refinamiento de Búsqueda

## Problema Identificado

El usuario reportó que cuando SIRIUS encuentra 4 títulos correctamente y luego el usuario intenta refinar la búsqueda diciendo "Estoy buscando el título que tiene la tasa facial del 14,2232%", SIRIUS:
- No mantiene el contexto de los 4 títulos encontrados
- Responde: "No se encontraron valoraciones para el nemotécnico CDTBGASOV. con vencimiento al 30/08/2027."
- Esto indica que está haciendo una nueva búsqueda en lugar de filtrar sobre los resultados previos

## Cambios Realizados

### 1. Mejora en la Extracción de Cupón/Tasa Facial

**Problema**: El valor "14,2232" usa coma como separador decimal, pero los patrones de regex solo manejaban puntos.

**Solución**: Se mejoraron los patrones de regex para manejar tanto comas como puntos como separadores decimales:

```python
# Antes:
cupon_patterns = [
    r'(?:tasa facial|cup[oó]n).*?(\d+\.?\d*)',
    # ...
]

# Después:
cupon_patterns = [
    r'(?:tasa facial|cup[oó]n).*?del (\d+[.,]\d+|\d+)',
    r'(?:tasa facial|cup[oó]n).*?(\d+[.,]\d+|\d+)',
    # ...
]

# Y luego normalizar:
cupon_str = match.group(1).replace(',', '.')
cupon_val = float(cupon_str)
```

### 2. Mejora en la Detección de Refinamiento

**Problema**: La detección de refinamiento no era suficientemente robusta para detectar mensajes como "Estoy buscando el título que tiene la tasa facial del 14,2232%".

**Solución**: Se mejoró la lógica de detección para incluir más frases de refinamiento:

```python
# Se añadieron más frases de detección:
tiene_frases_busqueda = any(frase in message_lower for frase in [
    "estoy buscando", "busco", "busca", "quiero el", "necesito el", 
    "el titulo que", "el título que", "titulo que tiene", "título que tiene"
])

# Y se añadieron frases adicionales en la condición de refinamiento:
any(frase in message_lower for frase in [
    "que tiene", "que tiene la", "que tenga", "con tasa", "con cupón",
    "título que", "titulo que"
])
```

### 3. Asegurar Filtrado sobre `last_results`

**Problema**: Cuando se detectaba refinamiento, a veces se ejecutaba una nueva consulta en lugar de filtrar sobre `last_results`.

**Solución**: Se mejoró la lógica para asegurar que cuando se detecta refinamiento:
- Se filtra sobre `last_results` por cupón/tasa facial
- Se actualiza `last_results` con los resultados filtrados
- Se actualiza `last_query` con el cupón agregado
- Se salta la ejecución de consulta normal y se continúa directamente con el procesamiento de resultados

## Archivos Modificados

- `backend/services/chat_service.py`:
  - Líneas 370-401: Mejora en extracción de cupón/tasa facial para manejar comas decimales
  - Líneas 425-455: Mejora en detección de refinamiento
  - Líneas 776-851: Mejora en filtrado sobre `last_results` cuando se detecta refinamiento

## Resultado Esperado

Ahora, cuando el usuario:
1. Hace una consulta que encuentra 4 títulos: "¿Cuál es la TIR de valoración de un CDTBGASOV con vencimiento del 30/08/2027?"
2. Luego refina diciendo: "Estoy buscando el título que tiene la tasa facial del 14,2232%"

SIRIUS debería:
- ✅ Detectar que es un refinamiento
- ✅ Extraer correctamente el cupón 14.2232 (de 14,2232)
- ✅ Filtrar los 4 títulos previos por tasa facial
- ✅ Mostrar solo el título que coincide con la tasa facial especificada
- ✅ NO hacer una nueva búsqueda

## Notas Técnicas

- Los patrones de regex ahora manejan tanto comas como puntos como separadores decimales
- La detección de refinamiento es más robusta y detecta múltiples formas de expresar refinamiento
- El filtrado sobre `last_results` se hace en memoria, evitando consultas innecesarias a la base de datos
- El contexto de la conversación se mantiene correctamente entre mensajes
