import { useCallback, useState, useMemo } from 'react';
import { GoogleMap, useLoadScript, MarkerF, InfoWindowF } from '@react-google-maps/api';
import PropTypes from 'prop-types';

const MapContainer = ({ properties }) => {
  const [map, setMap] = useState(null);
  const [selectedProperty, setSelectedProperty] = useState(null);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY,
    libraries: ['places']
  });

  const containerStyle = useMemo(() => ({
    width: '100%',
    height: '100vh'
  }), []);

  const center = useMemo(() => ({
    lat: 36.7783,
    lng: -119.4179
  }), []);

  const onLoad = useCallback((map) => {
    setMap(map);
  }, []);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  if (loadError) return <div>지도를 불러오는데 실패했습니다</div>;
  if (!isLoaded) return <div>지도를 불러오는 중...</div>;

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={6}
      onLoad={onLoad}
      onUnmount={onUnmount}
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
          <div style={{ maxWidth: '200px' }}>
            <h3>{selectedProperty.City}, {selectedProperty.State}</h3>
            <p>우편번호: {selectedProperty.zipcode}</p>
            <p style={{ fontWeight: 'bold', color: '#2b6cb0' }}>
              가격: ${selectedProperty.price.toLocaleString()}
            </p>
          </div>
        </InfoWindowF>
      )}
    </GoogleMap>
  );
};

MapContainer.propTypes = {
  properties: PropTypes.array.isRequired
};

export default MapContainer;
