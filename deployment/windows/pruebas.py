"""Suite compartida, con exclusiones explícitas de infraestructura exclusiva de Linux."""
from pathlib import Path
import sys
import unittest

raiz = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(raiz), str(raiz / 'tests')]
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for archivo in sorted((raiz / 'tests').glob('test_*.py')):
    if sys.platform == 'win32' and archivo.stem in ('test_auxiliar_empaquetado', 'test_recuperar_catalogo'):
        # Importan fcntl/pwd o el despliegue sudo de Raspberry Pi; se prueban en Linux.
        print('Solo Linux, no ejecutado en Windows:', archivo.stem)
        continue
    suite.addTests(loader.loadTestsFromName(archivo.stem))
resultado = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not resultado.wasSuccessful())
