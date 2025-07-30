"""Util"""


try:
    import importlib.resources

    _files = importlib.resources.files  # only valid in 3.9+
except AttributeError:
    import importlib_resources  # needs pip install

    _files = importlib_resources.files

files = _files('shaded')
data_dir = files / 'data'
data_dir_path = str(data_dir)
