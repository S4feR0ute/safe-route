import { useState, useRef, useEffect } from 'react';
import './RouteForm.css';

const RouteForm = ({ origen, destino, onClear, clearTrigger }) => {
  const [origenText, setOrigenText] = useState('');
  const [destinoText, setDestinoText] = useState('');
  const [sugOrigenActive, setSugOrigenActive] = useState(false);
  const [sugDestinoActive, setSugDestinoActive] = useState(false);
  const [sugOrigen, setSugOrigen] = useState([]);
  const [sugDestino, setSugDestino] = useState([]);
  const timeoutRef = useRef(null);

  useEffect(() => {
    setOrigenText('');
    setDestinoText('');
    setSugOrigen([]);
    setSugDestino([]);
  }, [clearTrigger]);

  const searchNominatim = async (query, setSuggestions) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const viewbox = '-77.2,-11.8,-76.8,-12.2';
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&viewbox=${viewbox}&bounded=1&countrycodes=pe`
      );
      const data = await response.json();
      setSuggestions(data);
    } catch (error) {
      console.error('Error en búsqueda:', error);
      setSuggestions([]);
    }
  };

  const handleOrigenChange = (e) => {
    const value = e.target.value;
    setOrigenText(value);
    setSugOrigenActive(true);

    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      searchNominatim(value, setSugOrigen);
    }, 300);
  };

  const handleDestinoChange = (e) => {
    const value = e.target.value;
    setDestinoText(value);
    setSugDestinoActive(true);

    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      searchNominatim(value, setSugDestino);
    }, 300);
  };

  const selectSuggestion = (suggestion, type) => {
    const coords = [parseFloat(suggestion.lat), parseFloat(suggestion.lon)];
    const displayName = suggestion.display_name.split(',')[0];

    if (type === 'origen') {
      setOrigenText(displayName);
      setSugOrigenActive(false);
      setSugOrigen([]);
      window.dispatchEvent(new CustomEvent('selectPoint', {
        detail: { type: 'origen', coords }
      }));
    } else {
      setDestinoText(displayName);
      setSugDestinoActive(false);
      setSugDestino([]);
      window.dispatchEvent(new CustomEvent('selectPoint', {
        detail: { type: 'destino', coords }
      }));
    }
  };

  const handleSubmit = (evento) => {
    evento.preventDefault();

    if (!origen || !destino) {
      alert('Por favor selecciona origen y destino');
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
          <label>Origen:</label>
          <div className="search-container">
            <input
              type="text"
              placeholder="Buscar dirección o hacer click en el mapa"
              value={origenText}
              onChange={handleOrigenChange}
              onFocus={() => setSugOrigenActive(true)}
              onBlur={() => setTimeout(() => setSugOrigenActive(false), 200)}
            />
            {sugOrigenActive && sugOrigen.length > 0 && (
              <ul className="suggestions-list">
                {sugOrigen.map((sug, idx) => (
                  <li key={idx} onClick={() => selectSuggestion(sug, 'origen')}>
                    {sug.display_name.split(',').slice(0, 2).join(',')}
                  </li>
                ))}
              </ul>
            )}
          </div>
          {origen && (
            <div className="coords-display">
              {formatCoords(origen)}
            </div>
          )}
        </div>

        <div className="campo-grupo">
          <label>Destino:</label>
          <div className="search-container">
            <input
              type="text"
              placeholder="Buscar dirección o hacer click en el mapa"
              value={destinoText}
              onChange={handleDestinoChange}
              onFocus={() => setSugDestinoActive(true)}
              onBlur={() => setTimeout(() => setSugDestinoActive(false), 200)}
            />
            {sugDestinoActive && sugDestino.length > 0 && (
              <ul className="suggestions-list">
                {sugDestino.map((sug, idx) => (
                  <li key={idx} onClick={() => selectSuggestion(sug, 'destino')}>
                    {sug.display_name.split(',').slice(0, 2).join(',')}
                  </li>
                ))}
              </ul>
            )}
          </div>
          {destino && (
            <div className="coords-display">
              {formatCoords(destino)}
            </div>
          )}
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