import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@contextmanager
def transaction(db: Session):
    """
    Context manager para manejar transacciones de forma segura.
    Automáticamente hace commit al salir sin error, rollback en excepción.
    """
    try:
        yield db
        db.commit()
        logger.debug("Transacción commiteada")
    except Exception as e:
        db.rollback()
        logger.error(f"Transacción revertida: {e}")
        raise
    finally:
        db.close()


@contextmanager
def transaction_no_close(db: Session):
    """
    Similar a transaction() pero no cierra la sesión.
    Útil cuando necesitas manejar múltiples transacciones en el mismo script.
    """
    try:
        yield db
        db.commit()
        logger.debug("Transacción commiteada")
    except Exception as e:
        db.rollback()
        logger.error(f"Transacción revertida: {e}")
        raise
