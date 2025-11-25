# Verificación y Ajuste de Columnas en Supabase

## Resumen

Se verificaron las columnas reales en las tablas `BD_PIP` y `BD_Precia` de Supabase y se ajustó el código para mapear correctamente los nombres de columnas.

## Columnas Reales Encontradas

### Tablas BD_PIP y BD_Precia

Las tablas tienen las siguientes columnas (en mayúsculas):

| Columna Supabase | Mapeo a Modelo | Tipo |
|-----------------|----------------|------|
| `ISIN` | `isin` | VARCHAR(12) |
| `EMISION` | `emisor` | VARCHAR(255) |
| `TIPO_ACTIVO` | `tipo_instrumento` | VARCHAR(50) |
| `PRECIO_LIMPIO` | `precio_limpio` | FLOAT |
| `PRECIO_SUCIO` | `precio_sucio` | FLOAT |
| `TIR` | `tasa` | FLOAT |
| `DURACION` | `duracion` | FLOAT |
| `DURACION_MOD` | - | FLOAT |
| `VENCIMIENTO` | `fecha_vencimiento` | DATE |
| `TASA_FACIAL` | `cupon` | FLOAT |
| `PERIODICIDAD` | `frecuencia_cupon` | VARCHAR(20) |
| `FECHA_VALORACION` | `fecha` | DATE |
| `FUENTE` | `proveedor` | VARCHAR(20) |
| `TIPO_ARCHIVO` | `archivo_origen` | VARCHAR(500) |
| `created_at` | `timestamp_ingesta` | TIMESTAMP |
| `CALIFICACION` | - | VARCHAR |
| `DIAS_AL_VENCIMIENTO` | - | INTEGER |
| `MONEDA` | - | VARCHAR |
| `NEMOTECNICO` | - | VARCHAR |
| `TIPO_ARCHIVO` | - | VARCHAR |
| `user_id` | - | VARCHAR |
| `id` | `id` | INTEGER (PK) |

## Cambios Realizados

### 1. Servicio de Supabase (`backend/services/supabase_service.py`)

- **Detección automática de columnas**: El código ahora detecta automáticamente las columnas disponibles en las tablas
- **Mapeo de nombres**: Se agregó mapeo para columnas en mayúsculas:
  - `TIPO_ARCHIVO` → `archivo_origen`
  - `FUENTE` → `proveedor`
  - `FECHA_VALORACION` → `fecha`
  - `created_at` → `timestamp_ingesta`
- **Manejo flexible**: El código busca variaciones de nombres de columnas y se adapta automáticamente

### 2. Servicio de Ingesta (`backend/services/ingestion_service.py`)

- **Mapeo de columnas de Supabase**: Se agregaron mapeos para todas las columnas en mayúsculas:
  - `ISIN` → `isin`
  - `EMISION` → `emisor`
  - `TIPO_ACTIVO` → `tipo_instrumento`
  - `PRECIO_LIMPIO` → `precio_limpio`
  - `PRECIO_SUCIO` → `precio_sucio`
  - `TIR` → `tasa`
  - `DURACION` → `duracion`
  - `VENCIMIENTO` → `fecha_vencimiento`
  - `TASA_FACIAL` → `cupon`
  - `PERIODICIDAD` → `frecuencia_cupon`
  - `FECHA_VALORACION` → `fecha`
- **Detección de fecha**: Mejorada la detección de columna de fecha para manejar `FECHA_VALORACION`

## Verificación

### Estado Actual

✅ **Conexión exitosa** a Supabase API  
✅ **Tablas detectadas**: BD_PIP y BD_Precia existen  
✅ **Columnas detectadas**: El código identifica correctamente las columnas en mayúsculas  
✅ **Listado de archivos**: Funciona correctamente, detectó archivos en ambas tablas

### Prueba de Conexión

Ejecutar:
```powershell
python scripts/test_supabase_connection.py
```

Resultado esperado:
```
[OK] CONEXION EXITOSA
[OK] Todas las tablas estan disponibles
Archivos en BD_PIP: X
Archivos en BD_Precia: X
```

## Notas Importantes

1. **Nombres en mayúsculas**: Las columnas en Supabase están en mayúsculas, pero el código las mapea automáticamente a los nombres del modelo en minúsculas.

2. **Columnas adicionales**: Las tablas tienen columnas adicionales que no se mapean directamente al modelo (como `CALIFICACION`, `DIAS_AL_VENCIMIENTO`, `MONEDA`, etc.). Estas se ignoran durante la ingesta.

3. **Compatibilidad**: El código mantiene compatibilidad con archivos Excel/CSV que usan nombres en formato mixto (ej: "Precio Limpio", "Fecha Valoración").

4. **Detección automática**: El código detecta automáticamente qué columnas están disponibles y se adapta, por lo que funciona tanto con las columnas en mayúsculas de Supabase como con las columnas en formato mixto de archivos.

## Próximos Pasos

1. ✅ Verificación de columnas completada
2. ✅ Mapeo de columnas implementado
3. ✅ Pruebas de conexión exitosas
4. ⏭️ Probar ingesta de datos desde Supabase
5. ⏭️ Verificar que los datos se procesan correctamente




