from .backend.app.api import app

__version__ = "0.0.1"


qeapp = {
    "app": app,
    "version": __version__,
    "title": "AiiDA Quantum ESPRESSO App",
    "description": (
        "AiiDA Quantum ESPRESSO App is a web application for managing "
        "and submitting Quantum ESPRESSO calculations using AiiDA."
    ),
    "logo": "logo.png",
}
