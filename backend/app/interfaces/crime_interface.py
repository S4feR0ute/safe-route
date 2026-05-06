from abc import ABC, abstractmethod

class ICrimeRepository(ABC):
    @abstractmethod
    def download_source(self) -> str:
        """Lógica para descargar el archivo Excel/CSV desde la fuente."""
        pass

    @abstractmethod
    def parse_source(self, file_path: str):
        """Lógica para limpiar y procesar el archivo Excel/CSV."""
        pass

    @abstractmethod
    def save_rates(self, data_list: list):
        """Lógica para persistir en la tabla district_crime_rates."""
        pass