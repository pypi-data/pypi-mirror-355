"""SliceSight-Next: Advanced Redis hotspot detection and analysis."""

from slicesight_next.metrics import (
    auto_ratio_thresh,
    calc_cv,
    calc_gini,
    chisq_p,
    crc16,
    load_ratio,
    redis_cluster_slot,
    verdict,
)

__version__ = "0.1.0"
__all__ = [
    "auto_ratio_thresh",
    "calc_cv",
    "calc_gini",
    "chisq_p",
    "crc16",
    "load_ratio",
    "redis_cluster_slot",
    "verdict",
]
