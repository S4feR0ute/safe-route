const API_URL = 'http://localhost:8000/api/v1/moderation';

export const getModerationQueue = async (token) => {
  const response = await fetch(`${API_URL}/queue`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al obtener la cola de moderación');
  return response.json(); // Devuelve { total: X, reports: [...] }
};

export const approveReport = async (reportId, token, reason = 'Aprobado') => {
  const response = await fetch(`${API_URL}/${reportId}/approve`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ status: 'validated', reason })
  });
  if (!response.ok) throw new Error('Error al aprobar el reporte');
  return response.json();
};

export const rejectReport = async (reportId, token, reason) => {
  const response = await fetch(`${API_URL}/${reportId}/reject`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ status: 'rejected', reason })
  });
  if (!response.ok) throw new Error('Error al rechazar el reporte');
  return response.json();
};