import { useState } from 'react';
import MapView from './components/MapView';
import RouteForm from './components/RouteForm';

function App() {
  const [origen, setOrigen] = useState(null);
  const [destino, setDestino] = useState(null);
  const [clearTrigger, setClearTrigger] = useState(0);

  const handleSelectPoint = (type, coords) => {
    if (type === 'origen') {
      setOrigen(coords);
    } else if (type === 'destino') {
      setDestino(coords);
    }
  };

  const clearPoints = () => {
    setOrigen(null);
    setDestino(null);
    setClearTrigger(prev => prev + 1);
  };

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100%' }}>
      <RouteForm 
        origen={origen} 
        destino={destino}
        onClear={clearPoints}
        clearTrigger={clearTrigger}
      />
      <MapView 
        origen={origen}
        destino={destino}
        onSelectPoint={handleSelectPoint}
      />
    </div>
  );
}

export default App;