# Corrección del Refinamiento por Cupón/Tasa Facial

## Problema Identificado

Cuando el usuario realizaba consultas secuenciales:

1. **Primera consulta**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
   - ✅ Funcionaba correctamente, encontraba 4 títulos

2. **Segunda consulta (refinamiento)**: "Estoy buscando el título que tiene la tasa facial del 14,2232%"
   - ❌ No encontraba resultados (0 títulos)

3. **Consulta completa**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027 y con tasa facial 14,2232%?"
   - ✅ Funcionaba correctamente, encontraba 1 título

### Causas del Problema

1. **Normalización del cupón**: El cupón del usuario ("14,2232%") no se normalizaba al formato de la base de datos ("14.2232")
2. **Campo cupón faltante en serialización**: La función `_valuation_to_dict` no incluía el campo `cupon` al serializar resultados, por lo que se perdía al guardar en `last_results`
3. **Comparación sin normalización**: Los cupones de los resultados previos no se normalizaban antes de comparar

## Soluciones Implementadas

### 1. Función de Normalización de Cupón

Se creó la función `normalize_cupon()` en `ChatService` que:
- Elimina el símbolo `%` si está presente
- Reemplaza comas por puntos (ej: "14,2232" → "14.2232")
- Convierte a float
- Maneja errores de forma segura

```python
def normalize_cupon(self, cupon_value) -> Optional[float]:
    """
    Normaliza el valor del cupón/tasa facial al formato de la base de datos.
    """
    if cupon_value is None:
        return None
    
    try:
        if isinstance(cupon_value, str):
            cupon_str = cupon_value.strip().replace('%', '').replace(' ', '')
            cupon_str = cupon_str.replace(',', '.')
            return float(cupon_str)
        elif isinstance(cupon_value, (int, float)):
            return float(cupon_value)
        else:
            return None
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error normalizando cupón '{cupon_value}': {str(e)}")
        return None
```

### 2. Normalización Aplicada en Todos los Puntos Críticos

La normalización se aplica en:
- ✅ Extracción del cupón desde el mensaje del usuario (patrones regex)
- ✅ Extracción del cupón desde el LLM
- ✅ Construcción final del `ValuationQuery`
- ✅ Deserialización del cupón desde el contexto
- ✅ Comparación en refinamiento (normaliza tanto query.cupon como cupones de resultados)
- ✅ Método `_filter_by_cupon`

### 3. Corrección Crítica: `_valuation_to_dict`

**Problema**: La función no incluía el campo `cupon` al serializar objetos Valuation.

**Solución**: Se agregó el campo `cupon` (y `fecha_vencimiento`) a la serialización:

```python
def _valuation_to_dict(self, valuation) -> Dict:
    # ... código existente ...
    
    # IMPORTANTE: Incluir campos adicionales necesarios para refinamiento
    if hasattr(valuation, "cupon") and valuation.cupon is not None:
        result["cupon"] = valuation.cupon
    if hasattr(valuation, "fecha_vencimiento") and valuation.fecha_vencimiento:
        result["fecha_vencimiento"] = valuation.fecha_vencimiento.isoformat()
    
    return result
```

También se agregó normalización para diccionarios que ya tienen cupón como string.

### 4. Logs Adicionales para Debugging

Se agregaron logs detallados para:
- Verificar que el cupón esté disponible en los resultados previos
- Mostrar el proceso de normalización
- Mostrar la comparación de cupones durante el filtrado

## Archivos Modificados

1. **`backend/services/chat_service.py`**:
   - Agregada función `normalize_cupon()`
   - Normalización aplicada en extracción de cupón
   - Normalización aplicada en refinamiento
   - Corrección de `_valuation_to_dict` para incluir cupón
   - Logs adicionales para debugging

## Cómo Probar

### Prueba Manual

1. Iniciar el servidor backend:
   ```powershell
   cd backend
   python -m uvicorn main:app --reload
   ```

2. Abrir la interfaz web en: `http://localhost:8000`

3. Realizar las consultas secuenciales:
   - **Primera consulta**: "¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?"
     - Debe encontrar 4 títulos
   
   - **Segunda consulta (refinamiento)**: "Estoy buscando el título que tiene la tasa facial del 14,2232%"
     - Debe encontrar 1 título (filtrado de los 4 anteriores)

### Verificación de Logs

Revisar los logs del servidor para verificar:
- ✅ "Cupón del query normalizado: 14,2232% → 14.2232"
- ✅ "Cupones encontrados en last_results: [ISIN=..., cupon=14.2232, ...]"
- ✅ "ISIN ... pasó el filtro: cupon=14.2232 está en rango [...]"

## Resultado Esperado

Después de estos cambios, el flujo debería funcionar así:

1. **Primera consulta**: Encuentra títulos y guarda resultados con cupón incluido
2. **Segunda consulta (refinamiento)**:
   - Detecta refinamiento correctamente
   - Normaliza "14,2232%" → `14.2232`
   - Accede al cupón de cada resultado en `last_results` (ahora disponible)
   - Normaliza cada cupón de los resultados
   - Compara valores normalizados
   - **Encuentra 1 título** ✅

## Notas Adicionales

- El sistema ahora maneja correctamente diferentes formatos de cupón:
  - "14,2232%" (coma y porcentaje)
  - "14.2232%" (punto y porcentaje)
  - "14,2232" (solo coma)
  - "14.2232" (solo punto)
  - 14.2232 (float)

- La tolerancia de comparación es de ±0.01 para manejar diferencias de redondeo

- El cupón se normaliza automáticamente antes de cualquier búsqueda o comparación

