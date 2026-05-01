import { useState } from 'react';
import './RouteForm.css'; // Importamos diseño

const RouteForm = () => {
  // useState crea dos variables en la memoria: 'origen' y 'destino'.
  // setOrigen y setDestino son las funciones que actualizan esa memoria.
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');

  // Esta función se ejecuta cuando se presiona el botón "Buscar"
  const handleSubmit = (evento) => {
    evento.preventDefault(); // Evita que la página web se recargue
    
    // Como no hay backend aún, solamente mostramos una alerta para comprobar que funciona
    alert(`Buscando ruta segura...\nOrigen: ${origen}\nDestino: ${destino}`);
    console.log("Datos enviados:", { origen, destino });
  };

  return (
    <div className="formulario-contenedor">
      <h2>SafeRoute Lima</h2>
      
      
      <form onSubmit={handleSubmit}>
        
        <div className="campo-grupo">
          <label htmlFor="origen">Punto de Origen:</label>
          <input 
            type="text" 
            id="origen"
            placeholder="Ej. UNI Puerta 3" 
            value={origen}
            /* onChange detecta cada letra que escribes y actualiza la memoria */
            onChange={(e) => setOrigen(e.target.value)} 
            required /* Hace que sea obligatorio llenarlo */
          />
        </div>

        <div className="campo-grupo">
          <label htmlFor="destino">Punto de Destino:</label>
          <input 
            type="text" 
            id="destino"
            placeholder="Ej. Estación Central Metropolitano" 
            value={destino}
            onChange={(e) => setDestino(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn-buscar">
          Buscar Ruta Segura
        </button>

      </form>
    </div>
  );
};

export default RouteForm;