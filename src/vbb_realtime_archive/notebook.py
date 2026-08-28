"""
notebook.py
-----------
Zentraler Einstiegspunkt für alle Notebooks.
Importiere einmalig am Anfang jedes Notebooks:

    from vbb_realtime_archive.notebook import *
    setup_plotting()
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from wgnd.inspect import (
    inspect,
    inspect_missing,
    inspect_duplicates,
    inspect_outliers,
    inspect_outlier_detail,
    inspect_correlations,
)
from wgnd.core._output import success, warn, log, info_box, show_df, section_header
from wgnd.core.config import cfg

from vbb_realtime_archive.config import PATHS, PROJECT_NAME, RANDOM_SEED
from vbb_realtime_archive.settings import setup_plotting

__all__ = [
    "pd", "np", "plt", "sns", "Path",
    "inspect", "inspect_missing", "inspect_duplicates",
    "inspect_outliers", "inspect_outlier_detail", "inspect_correlations",
    "success", "warn", "log", "info_box", "show_df", "section_header", "cfg",
    "PATHS", "PROJECT_NAME", "RANDOM_SEED", "setup_plotting",
]
