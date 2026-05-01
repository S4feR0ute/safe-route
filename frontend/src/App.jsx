import MapView from './components/MapView';
import RouteForm from './components/RouteForm';

function App() {
  return (
    // Se agrega position: relative para que el position: absolute del formulario funcione bien
    <div style={{ position: 'relative', height: '100vh', width: '100%' }}>
      
      
      <RouteForm/>
      
      
      <MapView/>
      
    </div>
  );
}

export default App;