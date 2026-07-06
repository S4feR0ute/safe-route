import { useState } from 'react';

const IncidentModal = ({ isOpen, onClose, onSubmit, coords, isAuthenticated }) => {
  const [tipo, setTipo] = useState('Robo a mano armada');
  const [descripcion, setDescripcion] = useState('');
  const [fecha, setFecha] = useState('');
  const [archivo, setArchivo] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        tipo,
        descripcion,
        fecha,
        archivo,
        lat: coords.lat,
        lng: coords.lng
      });
      // Si el envío es exitoso, se limpia todo y cerrar
      setDescripcion('');
      setFecha('');
      setArchivo(null);
      onClose();
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.6)', zIndex: 9999,
      display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      <div style={{
        background: 'white', padding: '25px', borderRadius: '10px', 
        width: '90%', maxWidth: '420px', boxShadow: '0 8px 20px rgba(0,0,0,0.2)'
      }}>
        <h3 style={{ marginTop: 0, color: '#dc3545', display: 'flex', alignItems: 'center', gap: '8px' }}>
           Reportar Incidencia
        </h3>
        
        <p style={{ fontSize: '13px', color: '#666', marginBottom: '20px', paddingBottom: '10px', borderBottom: '1px solid #eee' }}>
          <strong>Ubicación:</strong> Lat {coords.lat.toFixed(4)}, Lng {coords.lng.toFixed(4)}
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Tipo de Incidente</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}>
              <option value="Robo a mano armada">Robo a mano armada</option>
              <option value="Arrebato">Arrebato (celular/cartera)</option>
              <option value="Vandalismo">Vandalismo</option>
              <option value="Agresión">Agresión física</option>
              <option value="Zona oscura/Peligrosa">Zona oscura/Peligrosa</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Descripción (Opcional)</label>
            <textarea 
              value={descripcion} onChange={(e) => setDescripcion(e.target.value)} 
              rows="3" style={{ width: '100%', padding: '10px', boxSizing: 'border-box', borderRadius: '5px', border: '1px solid #ccc' }}
              placeholder="Ej: Dos sujetos en moto lineal interceptaron..."
            />
          </div>

          {/* usuarios logeados*/}
          {isAuthenticated ? (
            <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '8px', border: '1px dashed #28a745' }}>
              <p style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#28a745', fontWeight: 'bold' }}>
                 Reportando con identidad verificada
              </p>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Fecha exacta del suceso</label>
                <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', borderRadius: '5px', border: '1px solid #ccc' }} required />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Documento Sustentatorio (Opcional)</label>
                <p style={{ margin: '0 0 8px 0', fontSize: '11px', color: '#6c757d' }}>Sube tu denuncia policial en PDF o JPG (Máx 10MB) para que este reporte afecte el cálculo de rutas seguras.</p>
                <input type="file" onChange={(e) => setArchivo(e.target.files[0])} accept=".pdf, image/*" style={{ fontSize: '13px' }} />
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '12px', color: '#856404', backgroundColor: '#fff3cd', padding: '10px', borderRadius: '5px', fontStyle: 'italic' }}>
              Estás reportando de forma anónima (Modo 1). Para adjuntar una denuncia y afectar el algoritmo de rutas, debes iniciar sesión.
            </div>
          )}
          {/**/}

          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button type="button" onClick={onClose} disabled={loading} style={{ flex: 1, padding: '12px', background: '#e9ecef', color: '#333', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' }}>
              Cancelar
            </button>
            <button type="submit" disabled={loading} style={{ flex: 1, padding: '12px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '5px', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}>
              {loading ? 'Enviando...' : 'Enviar Reporte'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default IncidentModal;