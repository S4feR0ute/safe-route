import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getModerationQueue, approveReport, rejectReport } from '../services/moderationApi';

const ModerationPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const data = await getModerationQueue(token);
      setReports(data.reports || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      const token = localStorage.getItem('token');
      await approveReport(id, token, "Validado por Moderador");
      // Quitamos el reporte de la lista visualmente
      setReports(reports.filter(r => r.id !== id));
    } catch (err) {
      alert("Error: No tienes permisos o falló la conexión.");
    }
  };

  const handleReject = async (id) => {
    const reason = window.prompt("¿Motivo del rechazo? (Ej: Falso, Incompleto, Spam)");
    if (!reason) return; // Si cancela, no hacemos nada

    try {
      const token = localStorage.getItem('token');
      await rejectReport(id, token, reason);
      // Quitamos el reporte de la lista visualmente
      setReports(reports.filter(r => r.id !== id));
    } catch (err) {
      alert("Error: No tienes permisos o falló la conexión.");
    }
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', background: '#f8f9fa', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, color: '#333' }}>Panel de Moderación</h1>
        <Link to="/" style={{ padding: '10px 15px', background: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '5px' }}>
          Volver al Mapa
        </Link>
      </div>

      {error && <div style={{ padding: '15px', background: '#f8d7da', color: '#721c24', borderRadius: '5px', marginBottom: '20px' }}>{error}</div>}

      {loading ? (
        <p>Cargando reportes pendientes...</p>
      ) : reports.length === 0 ? (
        <div style={{ padding: '30px', background: 'white', borderRadius: '8px', textAlign: 'center', color: '#666', border: '1px solid #ddd' }}>
          <h3> ¡Cola vacía!</h3>
          <p>No hay incidentes pendientes de revisión.</p>
        </div>
      ) : (
        <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden', border: '1px solid #ddd', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ background: '#343a40', color: 'white' }}>
              <tr>
                <th style={{ padding: '15px' }}>Tipo</th>
                <th style={{ padding: '15px' }}>Modo</th>
                <th style={{ padding: '15px' }}>Descripción</th>
                <th style={{ padding: '15px' }}>Fecha Registro</th>
                <th style={{ padding: '15px' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} style={{ borderBottom: '1px solid #ddd' }}>
                  <td style={{ padding: '15px', fontWeight: 'bold', color: '#dc3545' }}>{report.incident_type}</td>
                  <td style={{ padding: '15px' }}>
                    <span style={{ padding: '4px 8px', background: '#e9ecef', borderRadius: '12px', fontSize: '12px' }}>
                      Modo {report.mode}
                    </span>
                  </td>
                  <td style={{ padding: '15px' }}>{report.description || 'Sin descripción'}</td>
                  <td style={{ padding: '15px' }}>{new Date(report.created_at).toLocaleDateString()}</td>
                  <td style={{ padding: '15px', display: 'flex', gap: '10px' }}>
                    <button onClick={() => handleApprove(report.id)} style={{ padding: '8px 12px', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>✅ Aprobar</button>
                    <button onClick={() => handleReject(report.id)} style={{ padding: '8px 12px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>❌ Rechazar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ModerationPage;