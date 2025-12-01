# Guía de Uso - S.I.R.I.U.S V4

## Ingesta de Datos

### Ingesta Manual desde Archivo Local

```bash
python scripts/ingest_file.py \
  --file ruta/al/archivo.xlsx \
  --provider PIP_LATAM \
  --fecha 2025-01-15
```

**Parámetros:**
- `--file`: Ruta al archivo (CSV o Excel)
- `--provider`: `PIP_LATAM` o `PRECIA`
- `--fecha`: Fecha de valoración (YYYY-MM-DD), opcional (usa hoy si no se especifica)

### Ingesta Automática desde SharePoint

```bash
python scripts/ingest_sharepoint.py \
  --folder "Valoraciones/2025" \
  --provider PRECIA \
  --file-extension xlsx
```

**Parámetros:**
- `--folder`: Carpeta en SharePoint (opcional)
- `--provider`: `PIP_LATAM` o `PRECIA`
- `--file-extension`: `xlsx`, `xls`, o `csv`
- `--fecha`: Fecha de valoración (opcional, intenta extraer del nombre)
- `--dry-run`: Solo lista archivos sin ingerir

### Ingesta vía API

```bash
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -F "file=@archivo.xlsx" \
  -F "provider=PIP_LATAM" \
  -F "fecha_valoracion=2025-01-15"
```

## Consultas en el Chat

### Ejemplos de Consultas

1. **Precio de un instrumento:**
   ```
   ¿Cuál es el precio limpio del TES CO000123 hoy en Precia?
   ```

2. **Comparación de proveedores:**
   ```
   Compara PIP Latam vs Precia para el ISIN CO000123456
   ```

3. **Múltiples ISINs:**
   ```
   Trae valoración de ayer para estos ISINs: CO000123456, CO000789012, CO000345678
   ```

4. **Análisis técnico:**
   ```
   Explica la diferencia entre los dos proveedores para CO000123456
   ```

5. **Búsqueda por emisor:**
   ```
   Muestra todas las valoraciones del emisor Banco de la República
   ```

6. **Rango de fechas:**
   ```
   Trae valoraciones de la última semana para CO000123456
   ```

### Filtros Rápidos en la Interfaz

La interfaz web incluye un panel de filtros que permite:
- Seleccionar fecha específica
- Filtrar por proveedor
- Especificar múltiples ISINs (separados por coma)

Los filtros se aplican automáticamente a las consultas.

## Consultas vía API

### Endpoint de Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuál es el precio limpio del TES CO000123 hoy en Precia?",
    "user": "trader1"
  }'
```

### Consulta Estructurada

```bash
curl "http://localhost:8000/api/v1/valuations?isin=CO000123456&proveedor=PRECIA&fecha=2025-01-15"
```

### Comparación de Proveedores

```bash
curl "http://localhost:8000/api/v1/valuations/compare?isin=CO000123456&fecha=2025-01-15"
```

### Alertas

```bash
curl "http://localhost:8000/api/v1/valuations/CO000123456/alerts?fecha=2025-01-15"
```

## Formato de Archivos de Valoración

### Columnas Requeridas

- **ISIN** (obligatorio): Código ISIN del instrumento
- **Fecha** o **Fecha Valoración**: Fecha de la valoración

### Columnas Opcionales (se normalizan automáticamente)

- **Emisor**: Nombre del emisor
- **Tipo** o **Tipo Instrumento**: Tipo de instrumento
- **Plazo**: Plazo del instrumento
- **Precio Limpio**: Precio limpio
- **Precio Sucio**: Precio sucio
- **Tasa**: Tasa de interés
- **Duración**: Duración del instrumento
- **Convexidad**: Convexidad
- **Fecha Vencimiento**: Fecha de vencimiento
- **Fecha Emisión**: Fecha de emisión
- **Valor Nominal**: Valor nominal
- **Cupón**: Tasa cupón
- **Frecuencia Cupón**: Frecuencia de pago de cupón

### Mapeo de Columnas

El sistema normaliza automáticamente nombres de columnas comunes. Si tu archivo usa nombres diferentes, puedes:

1. Renombrar las columnas en el archivo
2. Modificar `COLUMN_MAPPINGS` en `backend/services/ingestion_service.py`

## Interpretación de Respuestas

### Estructura de Respuesta del Chat

Cada respuesta incluye:

1. **Answer**: Respuesta principal en texto
2. **Data**: Datos estructurados (tablas, objetos)
3. **Recommendations**: 3 recomendaciones accionables
4. **Metadata**: Metadatos de la consulta

### Recomendaciones

Las recomendaciones siguen el formato:
```
Hallazgo → Acción sugerida
```

Ejemplos:
- "Diferencia significativa en precio (75 pb) → Revisar curvas y metodologías de ambos proveedores"
- "Falta valoración en PIP Latam → Verificar ingesta de archivos de este proveedor"

### Alertas

El sistema detecta automáticamente:
- Datos faltantes por proveedor
- Campos críticos faltantes (precio limpio, tasa)
- Inconsistencias entre proveedores

## Automatización

### Ingesta Diaria Automática

**Linux/Mac (cron):**
```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar diariamente a las 8 AM
0 8 * * * cd /ruta/a/SIRIUS-V4 && python scripts/ingest_sharepoint.py --provider PIP_LATAM
```

**Windows (Task Scheduler):**
1. Abrir Task Scheduler
2. Crear tarea básica
3. Configurar para ejecutar el script diariamente

### Monitoreo

Revisar logs del backend para:
- Errores de ingesta
- Consultas frecuentes
- Alertas de datos faltantes

## Mejores Prácticas

1. **Ingesta Regular**: Configurar ingesta automática diaria
2. **Validación**: Revisar alertas después de cada ingesta
3. **Comparación**: Siempre comparar ambos proveedores para decisiones críticas
4. **Trazabilidad**: Usar los metadatos (archivo origen, fecha) para auditoría
5. **Consultas Específicas**: Ser específico en las consultas para mejores resultados

## Troubleshooting

### No se encuentran valoraciones

1. Verificar que la ingesta se completó exitosamente
2. Verificar que el ISIN es correcto
3. Verificar que la fecha es correcta
4. Revisar logs de ingesta

### Respuestas incorrectas del chat

1. Reformular la consulta de manera más específica
2. Usar filtros en la interfaz
3. Verificar que hay datos en la base de datos
4. Revisar logs del backend

### Errores de ingesta

1. Verificar formato del archivo
2. Verificar que existe columna ISIN
3. Verificar permisos de archivo
4. Revisar logs detallados









