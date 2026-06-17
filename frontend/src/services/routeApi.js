const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Llama al endpoint de ruteo del backend. origen/destino son [lat, lon].
export async function fetchRoute(origen, destino) {
  const body = {
    origin: { lat: origen[0], lon: origen[1] },
    destination: { lat: destino[0], lon: destino[1] },
  };

  const response = await fetch(`${API_URL}/api/v1/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.error?.message || 'No se pudo calcular la ruta');
  }

  return data;
}
