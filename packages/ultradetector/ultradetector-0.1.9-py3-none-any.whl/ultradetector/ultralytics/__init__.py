# Ultralytics YOLO 🚀, AGPL-3.0 license

__version__ = "8.3.24"

import os

# Set ENV variables (place before imports)
if not os.environ.get("OMP_NUM_THREADS"):
    os.environ["OMP_NUM_THREADS"] = "1"  # default for reduced CPU utilization during training

from ultradetector.ultralytics.models import NAS, RTDETR, SAM, YOLO, FastSAM, YOLOWorld
from ultradetector.ultralytics.utils import ASSETS, SETTINGS
from ultradetector.ultralytics.utils.checks import check_yolo as checks
from ultradetector.ultralytics.utils.downloads import download

settings = SETTINGS
__all__ = (
    "__version__",
    "ASSETS",
    "YOLO",
    "YOLOWorld",
    "NAS",
    "SAM",
    "FastSAM",
    "RTDETR",
    "checks",
    "download",
    "settings",
)
