# 🔧 Corrección: SIRIUS debe mostrar valoraciones de ambos proveedores (PIP y Precia)

**Fecha:** 29 de noviembre de 2025  
**Problema reportado:** Cuando SIRIUS encuentra 1 título con valoraciones de ambos proveedores, solo muestra la información de Precia y no la de PIP.

---

## 🐛 Problema Identificado

### Solo Muestra un Proveedor

**Síntoma:**
- Usuario pregunta: "¿Cuál es la TIR de valoración de un CDTBBOS0V con vencimiento del 02/02/2027?"
- SIRIUS encuentra 1 título
- SIRIUS solo muestra valoración de Precia
- **Problema:** Debería mostrar valoraciones de ambos proveedores (PIP y Precia)

**Causa:** Cuando hay 1 valoración, no se verifica si hay otra del otro proveedor antes de mostrar resultados.

---

## ✅ Correcciones Implementadas

### 1. Verificar Otro Proveedor cuando hay 1 Valoración

**Archivo:** `backend/services/chat_service.py` (línea ~787)

**Cambio:** Cuando se encuentra exactamente 1 valoración y no se especificó proveedor en la query, ahora se busca también en el otro proveedor usando el ISIN encontrado:

```python
# IMPORTANTE: Si hay 1 valoración y no se especificó proveedor, buscar también en el otro proveedor
if len(valuations) == 1 and not query.proveedor:
    valuation_encontrada = valuations[0]
    isin_encontrado = valuation_encontrada.isin
    proveedor_encontrado = valuation_encontrada.proveedor
    
    # Determinar el otro proveedor
    otro_proveedor = Provider.PIP_LATAM if proveedor_encontrado == Provider.PRECIA else Provider.PRECIA
    
    # Buscar en el otro proveedor usando el ISIN encontrado
    query_otro_proveedor = ValuationQuery(
        isin=isin_encontrado,
        proveedor=otro_proveedor,
        fecha=query.fecha,
        fecha_vencimiento=query.fecha_vencimiento,
        cupon=query.cupon
    )
    otras_valuations = self.query_service.query_valuations(query_otro_proveedor, ...)
    if otras_valuations:
        valuations.extend(otras_valuations)  # Agregar valoración del otro proveedor
```

**Resultado:** Ahora cuando hay 1 valoración, se busca también en el otro proveedor y se muestran todas las valoraciones encontradas.

---

### 2. Mostrar Todas las Valoraciones cuando hay 1 Título

**Archivo:** `backend/services/chat_service.py` (línea ~882)

**Cambio:** Cuando hay 1 título pero múltiples valoraciones (de ambos proveedores), se muestran todas:

```python
if len(valuations) > 1:
    proveedores = set(v.proveedor for v in valuations)
    if len(proveedores) > 1:
        answer = f"Se encontró 1 título con valoraciones de {len(proveedores)} proveedores:\n\n"
    answer += self.format_valuation_table(valuations)  # Muestra todas las valoraciones
```

**Resultado:** Muestra todas las valoraciones en una tabla, permitiendo comparar ambos proveedores.

---

## 🔄 Flujo Corregido

### Antes (Solo mostraba Precia):
```
1. Usuario: "CDTBBOS0V con vencimiento 02/02/2027"
2. Busca en Supabase (ambos proveedores)
3. Encuentra 1 valoración de Precia
4. ❌ Muestra solo Precia
```

### Después (Muestra ambos proveedores):
```
1. Usuario: "CDTBBOS0V con vencimiento 02/02/2027"
2. Busca en Supabase (ambos proveedores)
3. Encuentra 1 valoración de Precia
4. ✅ Detecta que hay 1 valoración
5. ✅ Busca en el otro proveedor usando el ISIN encontrado
6. ✅ Encuentra valoración de PIP también
7. ✅ Muestra ambas valoraciones en la tabla
```

---

## 🧪 Escenarios de Prueba

### Escenario 1: Título con Valoraciones de Ambos Proveedores

**Consulta:** "¿Cuál es la TIR de valoración de un CDTBBOS0V con vencimiento del 02/02/2027?"
- ✅ SIRIUS encuentra 1 título
- ✅ Busca valoración de Precia
- ✅ Busca valoración de PIP usando el ISIN encontrado
- ✅ Muestra tabla con ambas valoraciones

**Resultado esperado:** Tabla con 2 filas (una por cada proveedor)

---

## 📝 Notas Técnicas

### Por qué Buscar Después

La búsqueda inicial en Supabase ya consulta ambos proveedores. Sin embargo, cuando solo se encuentra 1 resultado, se hace una verificación adicional para asegurar que se obtengan todas las valoraciones disponibles del otro proveedor.

### Optimización Futura

- La consulta inicial ya busca en ambos proveedores
- La búsqueda adicional solo se ejecuta cuando hay 1 resultado
- Esto asegura que no se pierdan valoraciones

---

*Última actualización: 29 de noviembre de 2025*

