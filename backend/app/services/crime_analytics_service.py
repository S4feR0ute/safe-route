from sqlalchemy.orm import Session
from app.models.crime_raw import CrimeRawData
from app.models.crime_stats import DistrictCrimeStats
from app.core.constants import CRIME_WEIGHTS_MAP
import pandas as pd
import numpy as np

class CrimeAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def process_crime_metrics(self):
        """
        Algoritmo de consolidación y normalización de tasas de criminalidad.
        Transforma datos históricos en índices de seguridad para el ruteo.
        """
        # 1. Extracción de datos crudos
        query = self.db.query(CrimeRawData)
        df_raw = pd.read_sql(query.statement, self.db.bind)

        if df_raw.empty:
            print("Advertencia: No se encontraron datos en crime_raw_data para procesar.")
            return

        df_raw['is_violent'] = df_raw['crime_type'].isin(CRIME_WEIGHTS_MAP.keys())

        # 2. Aplicar Ponderación por Peligrosidad 
        df_raw['weight'] = df_raw['crime_type'].map(CRIME_WEIGHTS_MAP).fillna(0.05)
        df_raw['weighted_score'] = df_raw['incident_count'] * df_raw['weight']

        # 3. Agregación Histórica Unificada
        stats = df_raw.groupby(['district_ubigeo', 'district_name']).agg(
            total_all=('incident_count', 'sum'),
            total_violent=('incident_count', lambda x: x[df_raw.loc[x.index, 'is_violent']].sum()),
            weighted_sum=('weighted_score', 'sum')
        ).reset_index()

        # 4. Normalización Estadística (Escala 0.0 a 1.0)
        stats['safety_index'] = np.sqrt(stats['weighted_sum'])
        
        max_idx = stats['safety_index'].max()
        min_idx = stats['safety_index'].min()
        
        if max_idx == min_idx:
            stats['final_rate'] = 0.5
        else:
            stats['final_rate'] = (stats['safety_index'] - min_idx) / (max_idx - min_idx)

        # 5. Persistencia de métricas condensadas
        self.update_stats_table(stats)
        
        print(f"Éxito: Índices de seguridad generados para {len(stats)} distritos.")

    def update_stats_table(self, stats_df):
        """Limpia y actualiza la tabla de estadísticas procesadas."""
        self.db.query(DistrictCrimeStats).delete()
        
        for _, row in stats_df.iterrows():
            stat_entry = DistrictCrimeStats(
                district_ubigeo=row['district_ubigeo'],
                district_name=row['district_name'],
                total_incidents_count=int(row['total_all']),
                violent_incidents_count=int(row['total_violent']),
                weighted_crime_rate=float(row['final_rate']),
            )
            self.db.add(stat_entry)
        
        self.db.commit()