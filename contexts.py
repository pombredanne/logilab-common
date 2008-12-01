try:
    from contextlib import contextmanager
except ImportError:
    # py < 2.5
    pass
else:
    
    import tempfile
    import shutil

    def tempdir():
        try:
            path = tempfile.mkdtemp()
            yield path
        finally:
            shutil.rmtree(path)

    # keep py < 2.4 syntax compat to avoid distribution pb
    tempdir = contextmanager(tempdir)

