import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import MapView from '../components/MapView';
import RouteForm from '../components/RouteForm';
import ResultsPanel from '../components/ResultsPanel';
import { fetchRoute } from '../services/routeApi';
import { isAuthenticated, logout } from '../services/authApi';

const MapPage = () => {
  const navigate = useNavigate();
  const [origen, setOrigen] = useState(null);
  const [destino, setDestino] = useState(null);
  const [clearTrigger, setClearTrigger] = useState(0);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuth = isAuthenticated();

  const handleSelectPoint = (type, coords) => {
    if (type === 'origen') {
      setOrigen(coords);
    } else if (type === 'destino') {
      setDestino(coords);
    }
  };

  const handleSearch = async () => {
    if (!origen || !destino) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoute(origen, destino);
      setRouteData(data);
    } catch (e) {
      setError(e.message);
      setRouteData(null);
    } finally {
      setLoading(false);
    }
  };

  const clearPoints = () => {
    setOrigen(null);
    setDestino(null);
    setRouteData(null);
    setError(null);
    setClearTrigger(prev => prev + 1);
  };

  const handleLogout = () => {
    logout();
    navigate(0); // Refresca la página para ocultar los botones de usuario
  };

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100%' }}>
      {/* Botones de Autenticación flotantes */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 1000, background: 'white', padding: '10px 15px', borderRadius: '8px', boxShadow: '0 2px 6px rgba(0,0,0,0.3)' }}>
        {isAuth ? (
           <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
             <span style={{ fontWeight: 'bold', color: '#333' }}>¡Hola, Ciudadano!</span>
             <button onClick={handleLogout} style={{ cursor: 'pointer', padding: '5px 10px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}>Cerrar Sesión</button>
           </div>
        ) : (
           <div style={{ display: 'flex', gap: '15px' }}>
             <Link to="/login" style={{ textDecoration: 'none', color: '#007bff', fontWeight: 'bold' }}>Iniciar Sesión</Link>
             <Link to="/register" style={{ textDecoration: 'none', color: '#28a745', fontWeight: 'bold' }}>Crear Cuenta</Link>
           </div>
        )}
      </div>

      <RouteForm
        origen={origen}
        destino={destino}
        onClear={clearPoints}
        clearTrigger={clearTrigger}
        onSearch={handleSearch}
        loading={loading}
        error={error}
      />
      <MapView
        origen={origen}
        destino={destino}
        onSelectPoint={handleSelectPoint}
        routeData={routeData}
      />
      <ResultsPanel routeData={routeData} />
    </div>
  );
};

export default MapPage;