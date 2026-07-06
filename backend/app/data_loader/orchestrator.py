import sys
import logging
from pathlib import Path
from typing import Callable, List, Optional

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.data_loader.seed_crime_weights import run_seed_crime_weights
from app.data_loader.ingest_street_graph import run_street_network_ingestion
from app.data_loader.assign_districts import run_district_assignment
from app.data_loader.ingest_sidpol import run_sidpol_ingestion
from app.data_loader.ingest_urban_context import run_context_ingestion
from app.data_loader.calculate_scores import run_score_calculation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataLoaderOrchestrator:
    """Orquestador para ejecutar los data loaders en el orden correcto."""

    def __init__(self):
        self.loaders: List[tuple[str, str, Callable]] = [
            ("seed_crime_weights", "Semilla de pesos por tipo de delito", run_seed_crime_weights),
            ("ingest_street_graph", "Grafo peatonal de OSM", run_street_network_ingestion),
            ("assign_districts", "Asignación de distritos (ST_Within)", run_district_assignment),
            ("ingest_sidpol", "Ingesta de criminalidad SIDPOL", run_sidpol_ingestion),
            ("ingest_urban_context", "POIs de contexto urbano", run_context_ingestion),
            ("calculate_scores", "Cálculo del score compuesto", run_score_calculation),
        ]
        self.completed: List[str] = []
        self.failed: List[tuple[str, str]] = []

    def run_all(self, skip_steps: Optional[List[str]] = None) -> bool:
        """Ejecuta todos los pasos en orden, saltando los indicados en skip_steps."""
        skip_steps = skip_steps or []
        steps = [slug for slug, _, _ in self.loaders if slug not in skip_steps]
        return self._run_steps(steps, title="INICIANDO ORQUESTADOR DE DATALOADERS")

    def run_specific(self, steps: List[str]) -> bool:
        """Ejecuta solo los pasos indicados, respetando el orden canónico."""
        valid = [slug for slug, _, _ in self.loaders]
        invalid = [s for s in steps if s not in valid]
        if invalid:
            logger.error(f"Pasos inválidos: {invalid}")
            logger.error(f"Pasos válidos: {valid}")
            return False

        ordered = [slug for slug in valid if slug in steps]
        return self._run_steps(ordered, title="EJECUTANDO PASOS ESPECÍFICOS")

    def list_steps(self):
        """Lista todos los pasos disponibles."""
        logger.info("Pasos disponibles (en orden de ejecución):")
        for i, (slug, description, _) in enumerate(self.loaders, 1):
            logger.info(f"  {i}. {slug} — {description}")

    def _run_steps(self, steps: List[str], title: str) -> bool:
        logger.info("=" * 60)
        logger.info(title)
        logger.info("=" * 60)

        by_slug = {slug: (description, func) for slug, description, func in self.loaders}

        for slug in steps:
            description, loader_func = by_slug[slug]
            logger.info(f"\n{'─' * 60}")
            logger.info(f"▶ Ejecutando: {slug} — {description}")
            logger.info(f"{'─' * 60}")

            try:
                loader_func()
                self.completed.append(slug)
                logger.info(f"✓ Completado: {slug}")
            except Exception as e:
                self.failed.append((slug, str(e)))
                logger.error(f"✗ FALLO: {slug}")
                logger.error(f"  Error: {e}")
                break

        logger.info(f"\n{'=' * 60}")
        logger.info("RESUMEN FINAL")
        logger.info(f"{'=' * 60}")
        logger.info(f"✓ Completados: {len(self.completed)}")
        for slug in self.completed:
            logger.info(f"  • {slug}")

        if self.failed:
            logger.error(f"✗ Fallidos: {len(self.failed)}")
            for slug, error in self.failed:
                logger.error(f"  • {slug}: {error}")
            return False

        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Orquestador de data loaders para SafeRoute"
    )
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los pasos en orden")
    parser.add_argument("--skip", nargs="+", help="Pasos a saltar (ej: --skip ingest_street_graph)")
    parser.add_argument("--only", nargs="+", help="Ejecutar solo estos pasos (ej: --only calculate_scores)")
    parser.add_argument("--list", action="store_true", help="Listar los pasos disponibles")

    args = parser.parse_args()
    orchestrator = DataLoaderOrchestrator()

    if args.list:
        orchestrator.list_steps()
    elif args.only:
        sys.exit(0 if orchestrator.run_specific(args.only) else 1)
    elif args.all:
        sys.exit(0 if orchestrator.run_all(skip_steps=args.skip) else 1)
    else:
        parser.print_help()
        logger.info("\nEjemplos de uso:")
        logger.info("  python -m app.data_loader.orchestrator --all")
        logger.info("  python -m app.data_loader.orchestrator --all --skip ingest_street_graph")
        logger.info("  python -m app.data_loader.orchestrator --only calculate_scores")
        logger.info("  python -m app.data_loader.orchestrator --list")
