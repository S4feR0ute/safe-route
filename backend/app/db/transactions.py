import functools
import inspect
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


def transactional(method):
    """
    Decorator para métodos de servicio: ejecuta el método dentro de una
    transacción. Equivale a envolver el cuerpo en `with transaction_no_close(self.db)`.
    """
    if inspect.iscoroutinefunction(method):
        @functools.wraps(method)
        async def async_wrapper(self, *args, **kwargs):
            with transaction_no_close(self.db):
                return await method(self, *args, **kwargs)
        return async_wrapper

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with transaction_no_close(self.db):
            return method(self, *args, **kwargs)
    return wrapper
