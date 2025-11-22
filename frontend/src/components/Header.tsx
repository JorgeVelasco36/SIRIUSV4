import React from 'react';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">S.I.R.I.U.S V4</h1>
        <p className="header-subtitle">Asistente Conversacional de Renta Fija Colombiana</p>
      </div>
    </header>
  );
};

export default Header;



