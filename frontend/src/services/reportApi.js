const API_URL = 'http://localhost:8000/api/v1/reports'; 

export const createIncidentReport = async (reportData, token = null) => {
  const formData = new FormData();

  // Enviamos los datos al backend
  formData.append('incident_type', reportData.tipo);
  formData.append('latitude', reportData.lat);
  formData.append('longitude', reportData.lng);
  
  if (reportData.descripcion) {
    formData.append('description', reportData.descripcion);
  }

  if (token) {
    if (reportData.fecha) formData.append('incident_date', reportData.fecha);
    if (reportData.archivo) formData.append('file', reportData.archivo);
  }

  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: headers,
    body: formData, 
  });

  if (!response.ok) {
    const errorData = await response.json();
    
    // detectar error
    if (errorData?.error?.details?.errors?.length > 0) {
      const mainError = errorData.error.details.errors[0];
      throw new Error(`Rechazado -> Campo ${mainError.field}: ${mainError.message}`);
    }

    if (errorData?.error?.message) {
      throw new Error(`Rechazado: ${errorData.error.message}`);
    }
    
    // Por si FastAPI manda su error por defecto
    if (Array.isArray(errorData?.detail) && errorData.detail.length > 0) {
        const mainError = errorData.detail[0];
        throw new Error(`Rechazado -> Campo ${mainError.loc.join(' > ')}: ${mainError.msg}`);
    }

    throw new Error(errorData?.detail || 'Error al enviar el reporte al servidor');
  }

  return response.json();
};

export const getIncidentReports = async () => {
  try {
    const response = await fetch(API_URL);
    if (!response.ok) {
      return []; // Si falla, regresamos un arreglo vacío
    }
    const data = await response.json();
    // Devuelve un objeto { total: X, reports: [...] }
    return data.reports || []; 
  } catch (error) {
    console.error("Error al obtener reportes:", error);
    return [];
  }
};