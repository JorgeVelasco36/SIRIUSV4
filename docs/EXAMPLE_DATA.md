# Ejemplo de Datos - S.I.R.I.U.S V4

## Formato de Archivos de Valoración

### Ejemplo CSV

```csv
ISIN,Emisor,Tipo Instrumento,Plazo,Precio Limpio,Precio Sucio,Tasa,Duración,Convexidad,Fecha Valoración
CO000123456,Banco de la República,TES,5 años,102.45,103.12,5.25,4.2,0.15,2025-01-15
CO000789012,Banco de Bogotá,BONO,3 años,98.32,99.01,6.10,2.8,0.08,2025-01-15
CO000345678,Bancolombia,CDT,1 año,100.00,100.00,4.50,0.95,0.02,2025-01-15
```

### Ejemplo Excel

Las columnas pueden tener nombres variados, el sistema las normaliza automáticamente:

**Columnas aceptadas:**
- ISIN / Código ISIN
- Emisor
- Tipo / Tipo Instrumento
- Plazo
- Precio Limpio
- Precio Sucio
- Tasa
- Duración
- Convexidad
- Fecha / Fecha Valoración
- Fecha Vencimiento
- Fecha Emisión
- Valor Nominal
- Cupón
- Frecuencia Cupón

## Estructura de Datos en Base de Datos

### Tabla: valuations

```sql
CREATE TABLE valuations (
    id SERIAL PRIMARY KEY,
    isin VARCHAR(12) NOT NULL,
    emisor VARCHAR(255),
    tipo_instrumento VARCHAR(50),
    plazo VARCHAR(50),
    precio_limpio FLOAT,
    precio_sucio FLOAT,
    tasa FLOAT,
    duracion FLOAT,
    convexidad FLOAT,
    fecha DATE NOT NULL,
    proveedor VARCHAR(20) NOT NULL,
    archivo_origen VARCHAR(500),
    timestamp_ingesta TIMESTAMP DEFAULT NOW(),
    fecha_vencimiento DATE,
    fecha_emision DATE,
    valor_nominal FLOAT,
    cupon FLOAT,
    frecuencia_cupon VARCHAR(20)
);
```

### Ejemplo de Registro

```json
{
  "id": 1,
  "isin": "CO000123456",
  "emisor": "Banco de la República",
  "tipo_instrumento": "TES",
  "plazo": "5 años",
  "precio_limpio": 102.45,
  "precio_sucio": 103.12,
  "tasa": 5.25,
  "duracion": 4.2,
  "convexidad": 0.15,
  "fecha": "2025-01-15",
  "proveedor": "PIP_LATAM",
  "archivo_origen": "valoraciones_2025-01-15.xlsx",
  "timestamp_ingesta": "2025-01-15T08:30:00Z"
}
```

## Consultas de Ejemplo

### Consulta Simple

**Input:**
```
¿Cuál es el precio limpio del TES CO000123456 hoy en Precia?
```

**Output esperado:**
```
Valoración para ISIN CO000123456
Proveedor: PRECIA
Fecha: 2025-01-15

Precio Limpio: 102.45
Precio Sucio: 103.12
Tasa: 5.2500%
Duración: 4.20

Archivo origen: valoraciones_2025-01-15.xlsx

Recomendaciones:
→ Diferencia moderada vs PIP_LATAM (14 pb) → Diferencia dentro de rangos normales
→ Datos completos disponibles → Validar con otro proveedor si es crítico
→ Valoración actualizada → Considerar para toma de decisiones
```

### Comparación de Proveedores

**Input:**
```
Compara PIP Latam vs Precia para el ISIN CO000123456
```

**Output esperado:**
```
Comparación de proveedores para ISIN CO000123456
Fecha: 2025-01-15

PIP Latam:
- Precio Limpio: 102.31
- Tasa: 5.2600%
- Duración: 4.18

Precia:
- Precio Limpio: 102.45
- Tasa: 5.2500%
- Duración: 4.20

Diferencias (Precia - PIP Latam):
- Precio Limpio: 0.14 puntos base
- Tasa: -0.0100%

Recomendaciones:
→ Diferencia moderada en precio (14 pb) → Diferencia dentro de rangos normales
→ Tasas consistentes entre proveedores → Validar metodología si diferencia es crítica
→ Considerar validar con tercer proveedor si la diferencia es crítica para la operación
```

## Datos de Prueba

Para crear datos de prueba, puedes usar este script Python:

```python
import pandas as pd
from datetime import date

# Crear DataFrame de ejemplo
data = {
    'ISIN': ['CO000123456', 'CO000789012', 'CO000345678'],
    'Emisor': ['Banco de la República', 'Banco de Bogotá', 'Bancolombia'],
    'Tipo Instrumento': ['TES', 'BONO', 'CDT'],
    'Plazo': ['5 años', '3 años', '1 año'],
    'Precio Limpio': [102.45, 98.32, 100.00],
    'Precio Sucio': [103.12, 99.01, 100.00],
    'Tasa': [5.25, 6.10, 4.50],
    'Duración': [4.2, 2.8, 0.95],
    'Convexidad': [0.15, 0.08, 0.02],
    'Fecha Valoración': [date.today()] * 3
}

df = pd.DataFrame(data)
df.to_excel('ejemplo_valoraciones.xlsx', index=False)
print("Archivo creado: ejemplo_valoraciones.xlsx")
```

## Validaciones

El sistema valida automáticamente:

1. **ISIN obligatorio**: Debe existir y tener formato válido
2. **Fecha válida**: Debe ser una fecha válida
3. **Proveedor válido**: Debe ser PIP_LATAM o PRECIA
4. **Tipos de datos**: Números para precios, tasas, etc.

## Errores Comunes

1. **ISIN faltante**: El archivo debe tener una columna ISIN
2. **Formato de fecha incorrecto**: Usar YYYY-MM-DD
3. **Columnas con nombres no reconocidos**: Ver mapeo en `IngestionService`
4. **Valores no numéricos**: Los campos numéricos deben ser números válidos









