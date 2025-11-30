import React from 'react';
import './ValuationTable.css';

interface ValuationData {
  isin?: string;
  proveedor?: string;
  fecha?: string;
  precio_limpio?: number;
  precio_sucio?: number;
  tasa?: number;
  duracion?: number;
  convexidad?: number;
  emisor?: string;
  tipo_instrumento?: string;
}

interface ValuationTableProps {
  data: ValuationData[];
}

const ValuationTable: React.FC<ValuationTableProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return null;
  }

  const formatNumber = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(decimals);
  };

  return (
    <div className="valuation-table-container">
      <table className="valuation-table">
        <thead>
          <tr>
            <th>ISIN</th>
            <th>Proveedor</th>
            <th>Fecha</th>
            <th>Precio Limpio</th>
            <th>Precio Sucio</th>
            <th>Tasa</th>
            <th>Duración</th>
            {data.some(d => d.convexidad) && <th>Convexidad</th>}
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr key={idx}>
              <td>{item.isin || 'N/A'}</td>
              <td>{item.proveedor || 'N/A'}</td>
              <td>{item.fecha || 'N/A'}</td>
              <td className="number">{formatNumber(item.precio_limpio)}</td>
              <td className="number">{formatNumber(item.precio_sucio)}</td>
              <td className="number">{formatNumber(item.tasa, 4)}</td>
              <td className="number">{formatNumber(item.duracion)}</td>
              {data.some(d => d.convexidad) && (
                <td className="number">{formatNumber(item.convexidad, 4)}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ValuationTable;








