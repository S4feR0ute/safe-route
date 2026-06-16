from abc import ABC, abstractmethod


class IDistrictDAO(ABC):
    @abstractmethod
    def extract_boundary(self, place_name: str, ubigeo: str):
        """
        Extrae el polígono límite de un distrito desde OpenStreetMap.
        Retorna un diccionario con 'ubigeo', 'name' y 'geometry' (WKT).
        """
        pass

    @abstractmethod
    def save_boundary(self, boundary_data: dict) -> bool:
        """
        Guarda el polígono de un distrito en la base de datos.
        Retorna True si se guardó, False si ya existía.
        """
        pass
