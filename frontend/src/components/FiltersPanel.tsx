import React from 'react';
import './FiltersPanel.css';

interface FiltersPanelProps {
  filters: {
    fecha: string;
    proveedor: string;
    isins: string;
  };
  onFiltersChange: (filters: any) => void;
}

const FiltersPanel: React.FC<FiltersPanelProps> = ({ filters, onFiltersChange }) => {
  const handleChange = (field: string, value: string) => {
    onFiltersChange({
      ...filters,
      [field]: value
    });
  };

  return (
    <div className="filters-panel">
      <h3>Filtros Rápidos</h3>
      
      <div className="filter-group">
        <label htmlFor="fecha">Fecha:</label>
        <input
          type="date"
          id="fecha"
          value={filters.fecha}
          onChange={(e) => handleChange('fecha', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label htmlFor="proveedor">Proveedor:</label>
        <select
          id="proveedor"
          value={filters.proveedor}
          onChange={(e) => handleChange('proveedor', e.target.value)}
        >
          <option value="">Todos</option>
          <option value="PIP_LATAM">PIP Latam</option>
          <option value="PRECIA">Precia</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="isins">ISINs (separados por coma):</label>
        <textarea
          id="isins"
          value={filters.isins}
          onChange={(e) => handleChange('isins', e.target.value)}
          placeholder="CO000123456, CO000789012"
          rows={3}
        />
      </div>

      <button
        className="clear-filters"
        onClick={() => onFiltersChange({ fecha: '', proveedor: '', isins: '' })}
      >
        Limpiar Filtros
      </button>
    </div>
  );
};

export default FiltersPanel;









