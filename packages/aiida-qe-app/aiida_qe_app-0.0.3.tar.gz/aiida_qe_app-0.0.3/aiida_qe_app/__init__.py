from aiida_qe_app.backend.app.api import app

__version__ = "0.0.3"


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
