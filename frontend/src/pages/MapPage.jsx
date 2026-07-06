import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import MapView from '../components/MapView';
import RouteForm from '../components/RouteForm';
import ResultsPanel from '../components/ResultsPanel';
import IncidentModal from '../components/IncidentModal';
import { fetchRoute } from '../services/routeApi';
import { isAuthenticated, logout } from '../services/authApi';
import { createIncidentReport, getIncidentReports } from '../services/reportApi';

const MapPage = () => {
  const navigate = useNavigate();
  const [origen, setOrigen] = useState(null);
  const [destino, setDestino] = useState(null);
  const [clearTrigger, setClearTrigger] = useState(0);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuth = isAuthenticated();

  // modal - reportes
  const [modalOpen, setModalOpen] = useState(false);
  const [reportCoords, setReportCoords] = useState(null);

  // Estado para guardar la lista de reportes
  const [reportsList, setReportsList] = useState([]);

  // Para mostrar/ocultar los pines
  const [showReports, setShowReports] = useState(true);

  // Cargar los reportes cuando la página inicia
  const fetchReports = async () => {
    const data = await getIncidentReports();
    setReportsList(data);
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Escuchar el evento de click derecho del mapa
  useEffect(() => {
    const handleOpenModal = (e) => {
      setReportCoords(e.detail);
      setModalOpen(true);
    };
    window.addEventListener('openIncidentModal', handleOpenModal);
    return () => window.removeEventListener('openIncidentModal', handleOpenModal);
  }, []);

  // Función para enviar el reporte al backend
  const handleSubmitReport = async (reportData) => {
    try {
      // Sacamos la llave (si existe) para saber si es Modo 1 o Modo 2/3
      const token = localStorage.getItem('token');
      await createIncidentReport(reportData, token);
      
      alert("¡Reporte enviado exitosamente a moderación!");
      await fetchReports();

    } catch (err) {
      throw err; // El Modal atrapará este error y lo mostrará en un alert
    }
  };

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
    navigate(0); // Actualizar la página
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

      <button
        onClick={() => setShowReports(!showReports)}
        style={{
          position: 'absolute', bottom: 30, right: 20, zIndex: 1000,
          padding: '12px 20px', background: showReports ? '#6c757d' : '#dc3545',
          color: 'white', border: 'none', borderRadius: '30px',
          boxShadow: '0 4px 10px rgba(0,0,0,0.3)', cursor: 'pointer',
          fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px'
        }}
      >
        {showReports ? 'Ocultar Alertas' : 'Mostrar Alertas'}
      </button>

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
        reports={reportsList}
        showReports={showReports}
      />
      
      <ResultsPanel routeData={routeData} />

      <IncidentModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmitReport}
        coords={reportCoords || { lat: 0, lng: 0 }}
        isAuthenticated={isAuth}
      />
    </div>
  );
};

export default MapPage;