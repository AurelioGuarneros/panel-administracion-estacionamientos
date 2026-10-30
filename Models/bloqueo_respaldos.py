"""Exclusión entre ventanas y procesos durante una actualización."""
from contextlib import contextmanager
import os


@contextmanager
def bloqueo(ruta):
    import fcntl
    descriptor = os.open(ruta, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('Hay una actualización en curso.') from None
        yield
    finally:
        os.close(descriptor)
