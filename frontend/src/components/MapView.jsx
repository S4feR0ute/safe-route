import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { useMapEvents, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const MapClickHandler = ({ onSelectPoint, origen, destino }) => {
  const map = useMap();

  useEffect(() => {
    const handleSelectPoint = (e) => {
      const { type, coords } = e.detail;
      onSelectPoint(type, coords);
      map.setView(coords, 14);
    };

    window.addEventListener('selectPoint', handleSelectPoint);
    return () => window.removeEventListener('selectPoint', handleSelectPoint);
  }, [onSelectPoint, map]);

  useMapEvents({
    click(e) {
      const coords = [e.latlng.lat, e.latlng.lng];
      
      if (!origen) {
        onSelectPoint('origen', coords);
      } else if (!destino) {
        onSelectPoint('destino', coords);
      }
    },
  });

  return null;
};

const FitRoute = ({ routeData }) => {
  const map = useMap();

  useEffect(() => {
    const features = routeData?.safe_route?.geojson?.features;
    if (!features?.length) return;
    const latlngs = features.flatMap((f) =>
      f.geometry.coordinates.map(([lon, lat]) => [lat, lon])
    );
    map.fitBounds(latlngs, { padding: [60, 60] });
  }, [routeData, map]);

  return null;
};

const MapView = ({ origen, destino, onSelectPoint, routeData }) => {
  const limaPosition = [-12.0464, -77.0428];

  const origenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const destinoIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  return (
    <MapContainer 
      center={limaPosition} 
      zoom={12} 
      style={{ height: '100vh', width: '100%' }} 
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      
      <MapClickHandler onSelectPoint={onSelectPoint} origen={origen} destino={destino} />
      
      {origen && (
        <Marker position={origen} icon={origenIcon}>
          <Popup>Origen</Popup>
        </Marker>
      )}
      
      {destino && (
        <Marker position={destino} icon={destinoIcon}>
          <Popup>Destino</Popup>
        </Marker>
      )}

      {routeData?.safe_route?.geojson?.features?.map((feature, idx) => {
        const positions = feature.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
        return (
          <Polyline
            key={idx}
            positions={positions}
            pathOptions={{ color: feature.properties.color, weight: 6, opacity: 0.85 }}
          >
            <Popup>
              {feature.properties.name}<br />
              Riesgo: {feature.properties.risk_score}
            </Popup>
          </Polyline>
        );
      })}

      <FitRoute routeData={routeData} />
    </MapContainer>
  );
};

export default MapView;