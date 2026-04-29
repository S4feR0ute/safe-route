import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css'; 

const MapView = () => {
  // Coordenadas oficiales de Lima, Perú [Latitud, Longitud]
  const limaPosition = [-12.0464, -77.0428];

  return (
    <MapContainer 
      center={limaPosition} 
      zoom={12} 
      // style hace que el mapa ocupe el 100% de la altura (100vh) y del ancho de la pantalla
      style={{ height: '100vh', width: '100%' }} 
    >
      {/* TileLayer se conecta a los servidores gratuitos de OpenStreetMap para descargar las fotos de las calles */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
    </MapContainer>
  );
};

export default MapView;