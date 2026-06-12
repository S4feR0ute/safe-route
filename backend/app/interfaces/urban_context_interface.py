from abc import ABC, abstractmethod
import geopandas as gpd

class IUrbanContextDAO(ABC):
    @abstractmethod
    def extract_pois(self, place_name: str, tags: dict) -> gpd.GeoDataFrame:
        """Extracts points of interest from OSM based on specific tags."""
        pass

    @abstractmethod
    def save_pois(self, gdf: gpd.GeoDataFrame, poi_type: str) -> None:
        """Persists the extracted POIs into the database."""
        pass