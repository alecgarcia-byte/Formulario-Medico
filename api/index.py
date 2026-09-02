"""
api/index.py
------------
Punto de entrada serverless para Vercel.

Agrega la raíz del proyecto a `sys.path` para que `backend` sea importable
como paquete y re-expone la aplicación FastAPI (`app`) que Vercel detecta
como ASGI. Todas las peticiones `/api/*` llegan aquí vía `vercel.json`.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.main import app  # noqa: E402,F401
