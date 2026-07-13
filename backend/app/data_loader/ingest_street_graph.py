import sys
import logging
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import osmnx as ox

from app.core.constants import TARGET_DISTRICTS
from app.db.session import SessionLocal
from app.models.street_network import StreetNode, StreetSegment
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO

logger = logging.getLogger(__name__)


def run_street_network_ingestion(districts=None, network_type="walk"):
    """
    Descarga la red peatonal de Lima Metropolitana + Callao como UN SOLO
    grafo (unión de los polígonos de todos los distritos) y la persiste.
    """
    districts = districts or TARGET_DISTRICTS
    db = SessionLocal()

    try:
        dao = OSMnxStreetGraphDAO(db=db, network_type=network_type)

        logger.info("--- Ingesta de red vial (OSMnx) ---")
        logger.info(f"Descarga UNIFICADA de {len(districts)} distritos | network_type={network_type}")
        logger.info("(una sola red con la unión de polígonos; la descarga puede tardar 10-30 min,")
        logger.info(" OSMnx cachea las respuestas de Overpass, así que reintentar es barato)")

        graph = dao.extract_graph(districts)

        # Nos quedamos con la componente fuertemente conexa principal:
        # descarta islotes no ruteables (pasajes privados, fragmentos de datos OSM).
        nodes_before = graph.number_of_nodes()
        graph = ox.truncate.largest_component(graph, strongly=True)
        kept_pct = 100 * graph.number_of_nodes() / nodes_before
        logger.info(
            f"Componente conexa principal: {graph.number_of_nodes()}/{nodes_before} "
            f"nodos ({kept_pct:.1f}%); {nodes_before - graph.number_of_nodes()} nodos aislados descartados"
        )
        if kept_pct < 90:
            logger.info(
                "  ADVERTENCIA: se descartó más del 10% de los nodos; revisa la "
                "descarga antes de continuar (¿faltaron distritos por geocodificar?)"
            )

        logger.info("\nLimpiando tablas de red vial...")
        logger.info("(el DELETE cascada también vacía risk_scores y urban_context:")
        logger.info(" después de esta ingesta ejecuta assign_districts y calculate_scores)")
        db.query(StreetSegment).delete()
        db.query(StreetNode).delete()
        db.commit()

        inserted = dao.save_graph(graph, "Lima Metropolitana + Callao")

        logger.info("\n--- Resumen ---")
        logger.info(f"Nodos: {graph.number_of_nodes()} | Segmentos insertados: {inserted}")
        logger.info("\nPróximos pasos (en este orden):")
        logger.info("  python -m app.data_loader.assign_districts")
        logger.info("  python -m app.data_loader.calculate_scores")

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    run_street_network_ingestion()
