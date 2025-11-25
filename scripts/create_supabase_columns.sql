-- Script SQL para crear las columnas necesarias en las tablas BD_PIP y BD_Precia
-- Ejecutar este script en el SQL Editor de Supabase

-- ============================================================
-- TABLA: BD_PIP
-- ============================================================

-- Columnas de identificación del instrumento
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS isin VARCHAR(12);
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS emisor VARCHAR(255);
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS tipo_instrumento VARCHAR(50);
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS plazo VARCHAR(50);

-- Columnas de valores de valoración
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS precio_limpio FLOAT;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS precio_sucio FLOAT;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS tasa FLOAT;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS duracion FLOAT;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS convexidad FLOAT;

-- Columnas de metadatos
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS fecha DATE;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS proveedor VARCHAR(20);
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS archivo_origen VARCHAR(500);
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS timestamp_ingesta TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Columnas adicionales normalizadas
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS fecha_vencimiento DATE;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS fecha_emision DATE;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS valor_nominal FLOAT;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS cupon FLOAT;
ALTER TABLE "BD_PIP" ADD COLUMN IF NOT EXISTS frecuencia_cupon VARCHAR(20);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_bd_pip_isin ON "BD_PIP"(isin);
CREATE INDEX IF NOT EXISTS idx_bd_pip_fecha ON "BD_PIP"(fecha);
CREATE INDEX IF NOT EXISTS idx_bd_pip_proveedor ON "BD_PIP"(proveedor);
CREATE INDEX IF NOT EXISTS idx_bd_pip_archivo_origen ON "BD_PIP"(archivo_origen);

-- ============================================================
-- TABLA: BD_Precia
-- ============================================================

-- Columnas de identificación del instrumento
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS isin VARCHAR(12);
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS emisor VARCHAR(255);
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS tipo_instrumento VARCHAR(50);
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS plazo VARCHAR(50);

-- Columnas de valores de valoración
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS precio_limpio FLOAT;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS precio_sucio FLOAT;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS tasa FLOAT;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS duracion FLOAT;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS convexidad FLOAT;

-- Columnas de metadatos
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS fecha DATE;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS proveedor VARCHAR(20);
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS archivo_origen VARCHAR(500);
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS timestamp_ingesta TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Columnas adicionales normalizadas
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS fecha_vencimiento DATE;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS fecha_emision DATE;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS valor_nominal FLOAT;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS cupon FLOAT;
ALTER TABLE "BD_Precia" ADD COLUMN IF NOT EXISTS frecuencia_cupon VARCHAR(20);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_bd_precia_isin ON "BD_Precia"(isin);
CREATE INDEX IF NOT EXISTS idx_bd_precia_fecha ON "BD_Precia"(fecha);
CREATE INDEX IF NOT EXISTS idx_bd_precia_proveedor ON "BD_Precia"(proveedor);
CREATE INDEX IF NOT EXISTS idx_bd_precia_archivo_origen ON "BD_Precia"(archivo_origen);

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
-- Para verificar que las columnas se crearon correctamente, ejecuta:
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name IN ('BD_PIP', 'BD_Precia')
-- ORDER BY table_name, ordinal_position;




