from contextlib import contextmanager
import tempfile
import shutil

@contextmanager
def tempdir(ignore_error=False, onerror=None):
    try:
        path = tempfile.mkdtemp()
        yield path
    finally:
        shutil.rmtree(path, ignore_error, onerror)
