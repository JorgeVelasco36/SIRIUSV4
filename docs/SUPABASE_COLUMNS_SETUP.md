# Configuración de Columnas en Supabase

## Problema Identificado

Las tablas `BD_PIP` y `BD_Precia` en Supabase actualmente solo tienen las columnas:
- `id` (auto-generada)
- `created_at` (timestamp automático)

Sin embargo, el código de SIRIUS espera las siguientes columnas para funcionar correctamente:

### Columnas Requeridas

#### Columnas de Identificación del Instrumento
- `isin` (VARCHAR(12)) - Código ISIN del instrumento
- `emisor` (VARCHAR(255)) - Nombre del emisor
- `tipo_instrumento` (VARCHAR(50)) - Tipo de instrumento (TES, BONO, CDT, etc.)
- `plazo` (VARCHAR(50)) - Plazo del instrumento

#### Columnas de Valores de Valoración
- `precio_limpio` (FLOAT) - Precio limpio
- `precio_sucio` (FLOAT) - Precio sucio
- `tasa` (FLOAT) - Tasa de interés
- `duracion` (FLOAT) - Duración del instrumento
- `convexidad` (FLOAT) - Convexidad del instrumento

#### Columnas de Metadatos
- `fecha` (DATE) - Fecha de valoración
- `proveedor` (VARCHAR(20)) - Proveedor (PIP_LATAM, PRECIA)
- `archivo_origen` (VARCHAR(500)) - Nombre del archivo origen
- `timestamp_ingesta` (TIMESTAMP WITH TIME ZONE) - Fecha y hora de ingesta

#### Columnas Adicionales Normalizadas
- `fecha_vencimiento` (DATE) - Fecha de vencimiento
- `fecha_emision` (DATE) - Fecha de emisión
- `valor_nominal` (FLOAT) - Valor nominal
- `cupon` (FLOAT) - Cupón
- `frecuencia_cupon` (VARCHAR(20)) - Frecuencia del cupón

## Solución

### Paso 1: Ejecutar Script SQL

Ejecuta el script SQL proporcionado en `scripts/create_supabase_columns.sql` desde el SQL Editor de Supabase:

1. Accede a tu proyecto en Supabase
2. Ve a "SQL Editor" en el menú lateral
3. Abre el archivo `scripts/create_supabase_columns.sql`
4. Copia y pega el contenido completo
5. Ejecuta el script

Este script:
- Crea todas las columnas necesarias en ambas tablas
- Crea índices para mejorar el rendimiento de las consultas
- Usa `IF NOT EXISTS` para evitar errores si las columnas ya existen

### Paso 2: Verificar Columnas

Después de ejecutar el script, puedes verificar que las columnas se crearon correctamente ejecutando:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('BD_PIP', 'BD_Precia')
ORDER BY table_name, ordinal_position;
```

### Paso 3: Probar la Conexión

Ejecuta el script de prueba:

```powershell
python scripts/test_supabase_connection.py
```

## Mejoras Implementadas en el Código

El código del servicio de Supabase (`backend/services/supabase_service.py`) ha sido mejorado para:

1. **Detección Automática de Columnas**: El código ahora detecta automáticamente qué columnas están disponibles en las tablas
2. **Manejo de Variaciones**: Soporta diferentes nombres de columnas (por ejemplo, `archivo_origen`, `archivo`, `file_name`)
3. **Mensajes de Error Mejorados**: Proporciona mensajes de error claros cuando faltan columnas, indicando qué script ejecutar
4. **Fallback a select=***: Si las columnas específicas no están disponibles, usa `select=*` como fallback

## Notas Importantes

- Las columnas deben crearse **antes** de intentar ingerir datos desde Supabase
- El script SQL es idempotente (puede ejecutarse múltiples veces sin problemas)
- Los índices mejoran significativamente el rendimiento de las consultas
- Si las tablas ya tienen datos, las nuevas columnas se crearán con valores `NULL` para los registros existentes

## Próximos Pasos

Una vez que las columnas estén creadas:

1. Verifica la conexión con `python scripts/test_supabase_connection.py`
2. Prueba listar archivos desde Supabase
3. Intenta ingerir datos desde Supabase usando el endpoint `/ingest`




