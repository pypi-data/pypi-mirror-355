from pathlib import Path

from platformdirs import user_cache_dir

from damply import __author__ as package_author
from damply import __name__ as package_name


def get_cache_dir() -> Path:
	"""
	Get the path to the cache directory for the package.

	Returns:
	    Path: The path to the cache directory.
	"""
	return Path(user_cache_dir(package_name, package_author))
