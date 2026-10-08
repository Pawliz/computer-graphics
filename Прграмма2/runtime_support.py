"""Поиск штатных библиотек Tcl/Tk для переносимых сборок Python под Windows."""
import os
from pathlib import Path
import sys


def configure_tk():
    # Некоторые переносимые сборки Tk не находят абсолютные пути с кириллицей.
    # Относительный путь ведёт к тем же библиотекам установленного Python.
    if sys.platform == "win32":
        base = Path(sys.base_prefix) / "tcl"
        for key, directory in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
            path = base / directory
            if key not in os.environ and path.is_dir():
                try:
                    os.environ[key] = os.path.relpath(path).replace("\\", "/")
                except ValueError:  # Python и проект находятся на разных дисках.
                    os.environ[key] = str(path)
