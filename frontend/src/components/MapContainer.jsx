import { useCallback, useState, useMemo } from 'react';
import { GoogleMap, useLoadScript, MarkerF, InfoWindowF } from '@react-google-maps/api';
import PropTypes from 'prop-types';
import MortgageBot from './MortgageBot';
import './MapContainer.css';

// 라이브러리 설정을 컴포넌트 외부로 이동
const libraries = ['places'];

// Google Maps 로드 설정을 메모이제이션
const mapOptions = {
  googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY,
  libraries
};

const MapContainer = ({ properties }) => {
  const [map, setMap] = useState(null);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [mortgageProperty, setMortgageProperty] = useState(null);

  // useLoadScript를 한 번만 호출하도록 설정
  const { isLoaded, loadError } = useLoadScript(mapOptions);

  const containerStyle = useMemo(() => ({
    width: '100%',
    height: '100vh'
  }), []);

  const center = useMemo(() => ({
    lat: 36.7783,
    lng: -119.4179
  }), []);

  const onLoad = useCallback((map) => {
    if (properties?.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      properties.forEach(property => {
        bounds.extend({
          lat: Number(property.latitude),
          lng: Number(property.longitude)
        });
      });
      map.fitBounds(bounds);
    }
    setMap(map);
  }, [properties]);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  if (loadError) {
    return <div>Error loading maps</div>;
  }

  if (!isLoaded) {
    return <div>Loading maps...</div>;
  }

  return (
    <>
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={6}
        onLoad={onLoad}
        onUnmount={onUnmount}
        options={{
          gestureHandling: 'greedy',
          disableDefaultUI: false,
        }}
      >
        {properties?.map((property) => (
          <MarkerF
            key={property.RegionID}
            position={{
              lat: Number(property.latitude),
              lng: Number(property.longitude)
            }}
            onClick={() => setSelectedProperty(property)}
          />
        ))}
        {selectedProperty && (
          <InfoWindowF
            position={{
              lat: Number(selectedProperty.latitude),
              lng: Number(selectedProperty.longitude)
            }}
            onCloseClick={() => setSelectedProperty(null)}
          >
            <div className="info-window-content">
              <h3>{selectedProperty.City}, {selectedProperty.State}</h3>
              <p>Price: ${selectedProperty.price.toLocaleString()}</p>
              <button 
                className="mortgage-consult-btn"
                onClick={() => setMortgageProperty(selectedProperty)}
              >
                Mortgage Consultation
              </button>
            </div>
          </InfoWindowF>
        )}
      </GoogleMap>

      {mortgageProperty && (
        <div className="mortgage-popup-overlay">
          <div className="mortgage-popup">
            <MortgageBot 
              onClose={() => setMortgageProperty(null)}
              propertyPrice={mortgageProperty.price}
              propertyAddress={`${mortgageProperty.City}, ${mortgageProperty.State}`}
            />
          </div>
        </div>
      )}
    </>
  );
};

MapContainer.propTypes = {
  properties: PropTypes.array.isRequired
};

export default MapContainer;
