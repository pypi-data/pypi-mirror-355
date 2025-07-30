"""
semantif package initialization.
Exports init() for configuration and judge() for semantic evaluation.
"""

from .config import init
from .core import judge

__all__ = ["init", "judge"]
