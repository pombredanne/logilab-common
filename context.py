from contextlib import contextmanager
import tempfile
import shutil

@contextmanager
def tempdir():
    try:
        path = tempfile.mkdtemp()
        yield path
    finally:
        shutil.rmtree(path)
