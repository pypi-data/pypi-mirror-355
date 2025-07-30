"""Package manager adapters for DepMan."""

from depman.adapters.base import PackageManagerAdapter
from depman.adapters.pip import PipAdapter
from depman.adapters.brew import BrewAdapter
from depman.adapters.npm import NpmAdapter

__all__ = ["PackageManagerAdapter", "PipAdapter", "BrewAdapter", "NpmAdapter"] 