import { useState, useEffect } from 'react';
import axios from 'axios';
import MapContainer from './components/MapContainer';
import Sidebar from './components/Sidebar';
import './App.css';

function App() {
  const [properties, setProperties] = useState([]);

  useEffect(() => {
    const fetchProperties = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/properties');
        console.log('Properties:', response.data); // 데이터 확인용 로그
        setProperties(response.data.properties);
      } catch (error) {
        console.error('Error fetching properties:', error);
      }
    };

    fetchProperties();
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <MapContainer properties={properties} />
    </div>
  );
}

export default App;
