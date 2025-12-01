# Instrucciones para Probar el Refinamiento por Cupón

## Objetivo de la Prueba

Verificar que las consultas secuenciales con refinamiento por cupón funcionen correctamente y encuentren el título esperado **COB13CD1K3N4**.

## Pasos para la Prueba

### 1. Iniciar el Servidor

```powershell
cd backend
python -m uvicorn main:app --reload
```

El servidor debería iniciarse en `http://localhost:8000`

### 2. Abrir la Interfaz Web

Abrir el navegador en: `http://localhost:8000`

### 3. Realizar la Primera Consulta

**Consulta:**
```
¿Cuál es la TIR de valoración de un CDTBGAS0V con vencimiento del 30/08/2027?
```

**Resultado Esperado:**
- ✅ Debe encontrar **4 títulos** que coinciden con el nemotécnico CDTBGAS0V y la fecha de vencimiento 30/08/2027
- ✅ El sistema debe mostrar un mensaje pidiendo más detalles para acotar la búsqueda
- ✅ Debe sugerir proporcionar el ISIN específico, emisor, o **tasa facial/cupón**

**Verificación:**
- Revisar que se muestren 4 títulos en los resultados
- Verificar que el sistema sugiera usar la tasa facial/cupón para refinar

### 4. Realizar la Segunda Consulta (Refinamiento)

**Consulta:**
```
Estoy buscando el título que tiene la tasa facial del 14,2232%
```

**Resultado Esperado:**
- ✅ Debe encontrar **1 título** (filtrado de los 4 anteriores)
- ✅ El ISIN debe ser: **COB13CD1K3N4**
- ✅ El cupón/tasa facial debe ser: **14.2232** (o muy cercano, con tolerancia de ±0.01)

**Verificación Detallada del Título COB13CD1K3N4:**

El resultado debe mostrar información del título con las siguientes características:

| Campo | Valor Esperado |
|-------|----------------|
| **ISIN** | COB13CD1K3N4 |
| **Cupón/Tasa Facial** | 14.2232 (o muy cercano) |
| **Nemotécnico** | CDTBGAS0V (o similar) |
| **Fecha de Vencimiento** | 30/08/2027 |
| **TIR** | Valor numérico (ej: ~10.4%) |
| **Precio Limpio** | Valor numérico |
| **Precio Sucio** | Valor numérico |
| **Duración** | Valor numérico |
| **Proveedor** | PIP_LATAM y/o PRECIA |

### 5. Verificar los Logs del Servidor

Revisar la consola del servidor para verificar que:

1. **Primera consulta:**
   - ✅ Detecta nemotécnico: CDTBGAS0V
   - ✅ Detecta fecha de vencimiento: 2027-08-30
   - ✅ Encuentra 4 títulos
   - ✅ Guarda resultados en `last_results` con cupón incluido

2. **Segunda consulta (refinamiento):**
   - ✅ Detecta refinamiento: "🔄 REFINAMIENTO DETECTADO"
   - ✅ Normaliza cupón: "14,2232%" → 14.2232
   - ✅ Log: "Cupón del query normalizado: 14,2232% → 14.2232"
   - ✅ Log: "Cupones encontrados en last_results: [ISIN=..., cupon=14.2232, ...]"
   - ✅ Log: "ISIN COB13CD1K3N4 pasó el filtro: cupon=14.2232 está en rango [...]"
   - ✅ Filtrado: "4 → 1 resultados"

## Posibles Problemas y Soluciones

### Problema: No encuentra resultados en la segunda consulta

**Síntomas:**
- Muestra "0 títulos encontrados"
- Mensaje: "No se encontraron títulos que coincidan con todos los criterios especificados"

**Verificaciones:**
1. Revisar logs del servidor para ver si:
   - El cupón se normalizó correctamente
   - Los resultados previos tienen cupón disponible
   - La comparación de cupones se realizó correctamente

2. Verificar en los logs:
   ```
   📋 Cupones encontrados en last_results: [ISIN=..., cupon=...]
   ```

3. Si los cupones no están disponibles, verificar que `_valuation_to_dict` incluya el campo `cupon`

### Problema: Error "cannot access local variable 'Provider'"

**Síntoma:**
- Error en la respuesta: "cannot access local variable 'Provider' where it is not associated with a value"

**Solución:**
- Ya corregido en el código (re-import de Provider en línea 1243)
- Si persiste, verificar que el servidor esté usando la versión más reciente del código

### Problema: Timeout en las consultas

**Síntoma:**
- Las consultas tardan más de 2 minutos
- Timeout error

**Solución:**
- Las consultas a Supabase pueden tardar varios minutos
- Aumentar el timeout del cliente o esperar a que complete
- Verificar la conexión a Supabase

## Resultado Esperado Final

Después de realizar ambas consultas secuenciales:

1. ✅ Primera consulta encuentra 4 títulos
2. ✅ Segunda consulta (refinamiento) encuentra 1 título
3. ✅ El título encontrado es **COB13CD1K3N4**
4. ✅ El cupón del título es **14.2232** (o muy cercano)
5. ✅ Se muestra información completa del título (TIR, precios, duración, etc.)

## Notas Adicionales

- El sistema normaliza automáticamente el cupón "14,2232%" a "14.2232" antes de buscar
- La tolerancia de comparación es de ±0.01 para manejar diferencias de redondeo
- El cupón se guarda en los resultados previos para permitir el refinamiento
- Los logs del servidor proporcionan información detallada del proceso de refinamiento

