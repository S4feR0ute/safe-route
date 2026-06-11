import './RouteForm.css';

const RouteForm = ({ origen, destino, onClear }) => {
  const handleSubmit = (evento) => {
    evento.preventDefault();
    
    if (!origen || !destino) {
      alert('Por favor selecciona origen y destino en el mapa');
      return;
    }

    alert(`Buscando ruta segura...\nOrigen: ${origen[0].toFixed(4)}, ${origen[1].toFixed(4)}\nDestino: ${destino[0].toFixed(4)}, ${destino[1].toFixed(4)}`);
    console.log("Datos enviados:", { origen, destino });
  };

  const formatCoords = (coords) => {
    if (!coords) return '-';
    return `${coords[0].toFixed(4)}, ${coords[1].toFixed(4)}`;
  };

  return (
    <div className="formulario-contenedor">
      <h2>SafeRoute Lima</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="campo-grupo">
          <label>Punto de Origen:</label>
          <div className="coords-display">
            {origen ? formatCoords(origen) : 'Haz click en el mapa'}
          </div>
        </div>

        <div className="campo-grupo">
          <label>Punto de Destino:</label>
          <div className="coords-display">
            {destino ? formatCoords(destino) : 'Haz click en el mapa'}
          </div>
        </div>

        <div className="button-group">
          <button type="submit" className="btn-buscar">
            Buscar Ruta Segura
          </button>
          {(origen || destino) && (
            <button type="button" className="btn-limpiar" onClick={onClear}>
              Limpiar
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default RouteForm;