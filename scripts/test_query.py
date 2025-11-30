#!/usr/bin/env python3
"""
Script para probar consultas a la base de datos
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Agregar directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Provider
from services.query_service import QueryService
from schemas import ValuationQuery


def test_query_by_isin(db: Session):
    """Prueba consulta por ISIN"""
    print("\n=== Prueba: Consulta por ISIN ===")
    query_service = QueryService(db)
    
    # Obtener un ISIN de ejemplo
    from models import Valuation
    sample = db.query(Valuation).first()
    if not sample:
        print("No hay datos en la base de datos")
        return
    
    isin = sample.isin
    print(f"Buscando ISIN: {isin}")
    
    query = ValuationQuery(isin=isin)
    results = query_service.query_valuations(query)
    
    print(f"Encontradas {len(results)} valoraciones:")
    for v in results:
        print(f"  - {v.isin} | {v.proveedor.value} | {v.fecha} | Precio: {v.precio_limpio}")


def test_compare_providers(db: Session):
    """Prueba comparación de proveedores"""
    print("\n=== Prueba: Comparación de Proveedores ===")
    query_service = QueryService(db)
    
    # Obtener un ISIN que tenga datos de ambos proveedores
    from models import Valuation
    from sqlalchemy import func
    
    isin_with_both = db.query(
        Valuation.isin
    ).group_by(Valuation.isin).having(
        func.count(func.distinct(Valuation.proveedor)) == 2
    ).first()
    
    if not isin_with_both:
        print("No hay ISINs con datos de ambos proveedores")
        return
    
    isin = isin_with_both[0]
    print(f"Comparando ISIN: {isin}")
    
    comparison = query_service.compare_providers(isin)
    
    if "error" in comparison:
        print(f"Error: {comparison['error']}")
        return
    
    print(f"Fecha: {comparison['fecha']}")
    if comparison['pip_latam']:
        print(f"PIP Latam - Precio: {comparison['pip_latam'].get('precio_limpio')}")
    if comparison['precia']:
        print(f"Precia - Precio: {comparison['precia'].get('precio_limpio')}")
    if comparison['diferencias']:
        print(f"Diferencias: {comparison['diferencias']}")


def test_query_by_date(db: Session):
    """Prueba consulta por fecha"""
    print("\n=== Prueba: Consulta por Fecha ===")
    query_service = QueryService(db)
    
    # Fecha de hoy
    today = date.today()
    print(f"Buscando valoraciones de: {today}")
    
    query = ValuationQuery(fecha=today)
    results = query_service.query_valuations(query)
    
    print(f"Encontradas {len(results)} valoraciones de hoy")
    
    # Rango de fechas (últimos 7 días)
    fecha_inicio = today - timedelta(days=7)
    print(f"\nBuscando valoraciones desde: {fecha_inicio} hasta: {today}")
    
    query = ValuationQuery(fecha_inicio=fecha_inicio, fecha_fin=today)
    results = query_service.query_valuations(query)
    
    print(f"Encontradas {len(results)} valoraciones en el rango")


def test_alerts(db: Session):
    """Prueba detección de alertas"""
    print("\n=== Prueba: Detección de Alertas ===")
    query_service = QueryService(db)
    
    # Obtener un ISIN de ejemplo
    from models import Valuation
    sample = db.query(Valuation).first()
    if not sample:
        print("No hay datos en la base de datos")
        return
    
    isin = sample.isin
    print(f"Verificando alertas para ISIN: {isin}")
    
    alerts = query_service.get_missing_data(isin)
    
    if alerts:
        print(f"Alertas encontradas ({len(alerts)}):")
        for alert in alerts:
            print(f"  - {alert}")
    else:
        print("No se encontraron alertas")


def main():
    db: Session = SessionLocal()
    try:
        # Verificar que hay datos
        from models import Valuation
        count = db.query(Valuation).count()
        print(f"Total de valoraciones en BD: {count}")
        
        if count == 0:
            print("\n⚠️  No hay datos en la base de datos.")
            print("   Ejecuta primero: python scripts/ingest_file.py --file <archivo> --provider <PROVEEDOR>")
            return
        
        # Ejecutar pruebas
        test_query_by_isin(db)
        test_compare_providers(db)
        test_query_by_date(db)
        test_alerts(db)
        
        print("\n[OK] Pruebas completadas")
        
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()








