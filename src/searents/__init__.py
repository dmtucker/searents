"""A Scraper of Seattle Rents"""

from pkg_resources import get_distribution

__all__ = [
    "__version__",
]
__version__ = get_distribution(__name__).version
