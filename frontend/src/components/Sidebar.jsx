import { useState } from 'react';
import PropTypes from 'prop-types';

function Sidebar({ properties, onFilter }) {
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [selectedCity, setSelectedCity] = useState('');

  // 고유한 도시 목록 생성
  const cities = [...new Set(properties.map(p => p.City))].sort();

  const handleFilter = () => {
    onFilter({
      minPrice: priceRange.min ? Number(priceRange.min) : null,
      maxPrice: priceRange.max ? Number(priceRange.max) : null,
      city: selectedCity
    });
  };

  return (
    <div className="sidebar">
      <h2>부동산 필터</h2>
      
      <div className="filter-section">
        <h3>가격 범위</h3>
        <div className="price-inputs">
          <input
            type="number"
            placeholder="최소 가격"
            value={priceRange.min}
            onChange={(e) => setPriceRange(prev => ({ ...prev, min: e.target.value }))}
          />
          <span>~</span>
          <input
            type="number"
            placeholder="최대 가격"
            value={priceRange.max}
            onChange={(e) => setPriceRange(prev => ({ ...prev, max: e.target.value }))}
          />
        </div>
      </div>

      <div className="filter-section">
        <h3>도시</h3>
        <select
          value={selectedCity}
          onChange={(e) => setSelectedCity(e.target.value)}
        >
          <option value="">모든 도시</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>

      <button onClick={handleFilter}>필터 적용</button>
    </div>
  );
}

Sidebar.propTypes = {
  properties: PropTypes.array.isRequired,
  onFilter: PropTypes.func.isRequired
};

export default Sidebar;