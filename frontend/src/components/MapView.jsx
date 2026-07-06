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
    
    contextmenu(e) {
      const coords = { lat: e.latlng.lat, lng: e.latlng.lng };
      // Avisamos a la página principal que abra la ventanita
      window.dispatchEvent(new CustomEvent('openIncidentModal', { detail: coords }));
    }
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

const MapView = ({ origen, destino, onSelectPoint, routeData, reports = [], showReports = true }) => {
  const limaPosition = [-12.0464, -77.0428];

  const origenIcon = L.divIcon({
    html: '<div style="font-size: 32px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin-top:-10px;">📍</div>',
    className: 'custom-emoji-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 20],
    popupAnchor: [0, -20],
  });

  const destinoIcon = L.divIcon({
    html: '<div style="font-size: 32px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin-top:-10px;">📍</div>',
    className: 'custom-emoji-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 20],
    popupAnchor: [0, -20],
  });

  const reportVerifiedIcon = L.divIcon({
    html: '<div style="font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.6); margin-top:-10px;">🚨</div>',
    className: 'custom-emoji-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });

  const reportPendingIcon = new L.divIcon({
    html: '<div style="font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.6); margin-top:-10px;">⚠️</div>',
    className: 'custom-emoji-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
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
      
      {showReports && reports.map((report) => {
        if (!report.latitude || !report.longitude) return null;
        
        const isVerified = report.status === 'validated';
        const position = [report.latitude, report.longitude];

        return (
          <Marker 
            key={report.id} 
            position={position} 
            icon={isVerified ? reportVerifiedIcon : reportPendingIcon}
          >
            <Popup>
              <strong>{isVerified ? '🚨' : '⚠️'} {report.incident_type}</strong><br/>
              <span style={{ fontSize: '11px', color: '#666' }}>
                Estado: {isVerified ? '✅ Verificado' : '⏳ Pendiente'}
              </span>
              {report.description && <p style={{ margin: '5px 0' }}>{report.description}</p>}
            </Popup>
          </Marker>
        );
      })}

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