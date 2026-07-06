// La dirección donde el backend de Jharvy está escuchando
const API_URL = 'http://localhost:8000/api/v1/auth'; 

export const login = async (email, password) => {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', // Le decimos que enviaremos un JSON
    },
    body: JSON.stringify({
      email: email,
      password: password
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    
    // detector de errores
    if (errorData?.error?.details?.errors?.length > 0) {
      const mainError = errorData.error.details.errors[0];
      throw new Error(`Rechazado -> ${mainError.field}: ${mainError.message}`);
    }
    if (errorData?.error?.message) {
      throw new Error(`Rechazado: ${errorData.error.message}`);
    }
    if (Array.isArray(errorData?.detail) && errorData.detail.length > 0) {
        const mainError = errorData.detail[0];
        throw new Error(`Rechazado -> Campo ${mainError.loc.join(' > ')}: ${mainError.msg}`);
    }
    
    throw new Error(errorData?.detail || 'Credenciales incorrectas');
  }

  const data = await response.json();
  // Guardamos la llave (JWT)
  localStorage.setItem('token', data.access_token); 
  return data;
};

export const registerUser = async (email, password, displayName) => {
  const response = await fetch(`${API_URL}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,
      display_name: displayName
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    
    // Leemos el formato de error
    if (errorData?.error?.details?.errors?.length > 0) {
      const mainError = errorData.error.details.errors[0];
      throw new Error(`Rechazado -> ${mainError.field}: ${mainError.message}`);
    }
    if (errorData?.error?.message) {
      throw new Error(`Rechazado: ${errorData.error.message}`);
    }
    if (Array.isArray(errorData?.detail) && errorData.detail.length > 0) {
        const mainError = errorData.detail[0];
        throw new Error(`Rechazado -> Campo ${mainError.loc.join(' > ')}: ${mainError.msg}`);
    }
    
    throw new Error(errorData?.detail || 'Error al registrar el usuario');
  }

  return response.json();
};

export const logout = () => {
  localStorage.removeItem('token'); // Borramos la llave para cerrar sesión
};

export const isAuthenticated = () => {
  return localStorage.getItem('token') !== null; // Comprueba si tenemos la llave guardada
};