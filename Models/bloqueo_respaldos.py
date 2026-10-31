"""Exclusión entre ventanas y procesos durante una actualización."""
from contextlib import contextmanager
import os


@contextmanager
def bloqueo(ruta):
    descriptor = os.open(ruta, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            if os.name == 'nt':
                import msvcrt
                # Bloquear el primer byte; Windows permite bloquear más allá de EOF.
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, PermissionError):
            raise RuntimeError('Hay una actualización en curso.') from None
        yield
    finally:
        os.close(descriptor)
