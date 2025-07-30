try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'jupyterlab_examples_hello_world' outside a proper installation.")
    __version__ = "dev"

from .installation.installation_flow import setup_handlers

def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyter_pieces"
    }]

def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_pieces"
    }]


def _load_jupyter_server_extension(server_app):
    """
    Registers the API handler to receive HTTP requests from the frontend extension.
    """
    setup_handlers(server_app.web_app)
