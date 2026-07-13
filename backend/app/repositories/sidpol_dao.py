import os
import logging
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import SIDPOL_SOURCE_URL
from app.models.crime_raw import CrimeRawData

logger = logging.getLogger(__name__)


class SIDPOLCrimeDAO:
    def __init__(self, db: Session):
        self.db = db
        self.source_url = SIDPOL_SOURCE_URL

    def download_source(self) -> str:
        """Descarga el archivo de SIDPOL y lo guarda localmente, retornando la ruta del archivo."""
        base_download_path = os.getenv("DOWNLOAD_PATH", "data/downloads")
        download_dir = os.path.join(os.getcwd(), base_download_path)
        os.makedirs(download_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        file_path = os.path.join(download_dir, f"sidpol_sync_{timestamp}.xlsx")

        if os.path.exists(file_path):
            logger.info(f"Usando cache: {file_path}")
            return file_path

        logger.info(f"Descargando desde: {self.source_url}")
        response = requests.get(self.source_url, timeout=60, verify=False)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Archivo guardado: {file_path}")
        return file_path

    def parse_source(self, file_path: str):
        # 1. Leer hojas relevantes (2025 y 2026)
        df_2025 = pd.read_excel(file_path, sheet_name='Temp6')
        df_2026 = pd.read_excel(file_path, sheet_name='Temp7')
        df_combined = pd.concat([df_2025, df_2026], ignore_index=True)
        
        # 2. Filtro Geográfico
        target_regions = ['LIMA', 'CALLAO']
        df_geo = df_combined[df_combined['PROV_HECHO'].isin(target_regions)].copy()

        # 3. Agrupación Anual por Distrito y Ubigeo
        summary = df_geo.groupby(['ANIO', 'UBIGEO_HECHO', 'DIST_HECHO', 'SUB_TIPO']).agg(
            total_anual=('n_dist_ID_DGC', 'sum')
        ).reset_index()
        
        return summary

    def save_rates(self, summary_df):
        self.db.query(CrimeRawData).delete()
        
        for _, row in summary_df.iterrows():
            crime_entry = CrimeRawData(
                district_ubigeo=str(row['UBIGEO_HECHO']),
                district_name=row['DIST_HECHO'],
                period=row['ANIO'],
                crime_type=row['SUB_TIPO'],
                incident_count=row['total_anual']
            )
            self.db.add(crime_entry)
        self.db.commit()