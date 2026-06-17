import { useState } from 'react';
import MapView from './components/MapView';
import RouteForm from './components/RouteForm';
import ResultsPanel from './components/ResultsPanel';
import { fetchRoute } from './services/routeApi';

function App() {
  const [origen, setOrigen] = useState(null);
  const [destino, setDestino] = useState(null);
  const [clearTrigger, setClearTrigger] = useState(0);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100%' }}>
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
}

export default App;
