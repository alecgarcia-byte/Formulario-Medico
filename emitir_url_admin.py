"""
emitir_url_admin.py
-------------------
Genera una URL de acceso al panel admin (token JWT de acceso único).

Uso:
    python emitir_url_admin.py [días_de_vida]

El script emite un JWT firmado con JWT_SECRET, con `sub=admin`, `exp` y un
`jti` único (registrado en `admin_sessions` para permitir revocación). La URL
resultante es `/admin-<jwt>` y es la ÚNICA forma de acceso al panel.

Requisitos previos:
    - Las variables SEGURAS deben estar configuradas en el entorno o `.env`
      (JWT_SECRET, y opcionalmente la conexión DATABASE_URL para persistir
      la sesión y permitir revocación).
"""

from __future__ import annotations

import argparse
import os
import sys

# Aseguramos que `backend` sea importable desde la raíz del proyecto.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera una URL de acceso al panel admin (JWT de acceso único)."
    )
    parser.add_argument(
        "dias",
        nargs="?",
        type=int,
        default=30,
        help="Días de vida del acceso (por defecto 30).",
    )
    args = parser.parse_args()

    if args.dias <= 0:
        parser.error("Los días de vida deben ser > 0.")

    from backend import config as app_config
    from backend.utils.auth import emitir_jwt_acceso

    base = (app_config.frontend_url() or "").rstrip("/")
    if not base:
        base = "https://formulario-medico.vercel.app"
        print("AVISO: FRONTEND_URL no configurado; se usa el dominio base por defecto.")

    token = emitir_jwt_acceso(
        expira_minutos=args.dias * 24 * 60
    )
    print("\n=== URL de acceso al panel admin (única) ===")
    print(f"\n  {base}/admin-{token}\n")
    print(f"  Vida del acceso: {args.dias} día(s)")
    print(
        "  Guarda esta URL en un lugar seguro. "
        "Para revocarla, marca revocado=1 su jti en admin_sessions.\n"
    )


if __name__ == "__main__":
    _main()