"""naQV - naru Query Viewport for ECOS API."""

from .client import EcosClient
from .models import StatisticItem, StatisticTable, KeyStatistic, StatisticData

__version__ = "0.1.0"
__all__ = ["EcosClient", "StatisticItem", "StatisticTable", "KeyStatistic", "StatisticData"]
