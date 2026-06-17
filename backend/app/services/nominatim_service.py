import requests
from app.core.constants import NOMINATIM_URL, HEADERS, MAX_RESULTS, LIMA_VIEWBOX


class NominatimService:
    """
    Servicio de geocodificación usando la API pública de Nominatim (OSM).
    """

    def buscar(self, query: str) -> list[dict]:
        """
        Busca una dirección o lugar y devuelve hasta MAX_RESULTS candidatos.
        """
        if not query or not query.strip():
            return []

        params = {
            "q":          query.strip(),
            "format":     "json",
            "limit":      MAX_RESULTS,
            "countrycodes": "pe",       # solo Perú
            "viewbox":    LIMA_VIEWBOX, # bounding box de Lima+Callao
            "bounded":    1,            # solo resultados dentro del viewbox
        }

        try:
            response = requests.get(
                NOMINATIM_URL,
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            response.raise_for_status()

            raw = response.json()

            # Parsear solo los campos que necesitamos
            resultados = []
            for item in raw:
                resultados.append({
                    "display_name": item.get("display_name", ""),
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                })

            return resultados

        except requests.exceptions.Timeout:
            raise TimeoutError("Nominatim no respondió a tiempo. Intenta de nuevo.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al conectarse con Nominatim: {e}")

    def geocodificar_direccion(self, direccion: str) -> dict | None:
        """
        Versión simplificada: devuelve solo el primer resultado o None.
        """
        resultados = self.buscar(direccion)
        if not resultados:
            return None
        return resultados[0]
