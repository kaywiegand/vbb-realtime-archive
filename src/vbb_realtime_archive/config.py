"""
config.py
---------
Zentrale Projektkonfiguration: Pfade, Konstanten, Umgebungsvariablen.

Importiere dieses Modul in Notebooks oder Scripts:
    from vbb_realtime_archive.config import PATHS, PROJECT_NAME
"""

from pathlib import Path

# ─── Projektname ───────────────────────────────────────────────────────────
PROJECT_NAME = "VBB Realtime Archive"
RANDOM_SEED = 42

# ─── Verzeichnisse ─────────────────────────────────────────────────────────
# Basis ist das Verzeichnis, in dem config.py liegt → 2 Ebenen nach oben
_SRC = Path(__file__).resolve().parent.parent.parent

PATHS = {
    "root":      _SRC,
    "data":      _SRC / "data",
    "raw":       _SRC / "data" / "raw",
    "interim":   _SRC / "data" / "interim",
    "processed": _SRC / "data" / "processed",
    "models":    _SRC / "models",
    "public":    _SRC / "public",
    "figures":   _SRC / "public" / "img",
    "configs":   _SRC / "configs",
}

# ─── Modell-Konstanten ──────────────────────────────────────────────────────
TEST_SIZE   = 0.2
VAL_SIZE    = 0.1
N_CV_FOLDS  = 5
