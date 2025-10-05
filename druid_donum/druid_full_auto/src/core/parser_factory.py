"""
ParserFactory - Factory pattern for creating site-specific parsers.

This module provides a centralized way to instantiate crawler objects based on
site names or configuration. It decouples the UI/engine from knowing which
concrete crawler classes exist.

Example:
    >>> from src.core.parser_factory import ParserFactory
    >>> factory = ParserFactory()
    >>> crawler = factory.create_crawler('forest_korea', config)
    >>> items = crawler.parse_list(soup)
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import importlib
import sys

from .base_crawler import BaseCrawler


class CrawlerNotFoundError(Exception):
    """Raised when a crawler plugin cannot be found or loaded."""
    pass


class ParserFactory:
    """
    Factory for creating BaseCrawler instances.

    This class handles dynamic loading of crawler plugins and provides a
    consistent interface for instantiating them.
    """

    def __init__(self, plugins_dir: str = "src/plugins"):
        """
        Initialize the factory.

        Args:
            plugins_dir: Directory where plugin modules are located
        """
        self.plugins_dir = Path(plugins_dir)
        self._crawler_cache: Dict[str, type] = {}

    def create_crawler(
        self,
        site_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseCrawler:
        """
        Create a crawler instance for the specified site.

        Args:
            site_name: Name of the site plugin (e.g., 'forest_korea')
            config: Optional configuration dict to pass to the crawler

        Returns:
            An instance of a BaseCrawler subclass

        Raises:
            CrawlerNotFoundError: If the plugin doesn't exist or can't be loaded
            TypeError: If the crawler class doesn't inherit from BaseCrawler

        Example:
            >>> factory = ParserFactory()
            >>> crawler = factory.create_crawler('forest_korea')
            >>> soup = crawler.fetch_page(url, params)
        """
        crawler_class = self._load_crawler_class(site_name)

        # Instantiate with config if provided
        if config:
            return crawler_class(config=config)
        else:
            return crawler_class()

    def _load_crawler_class(self, site_name: str) -> type:
        """
        Dynamically load a crawler class from a plugin module.

        Args:
            site_name: Name of the plugin module

        Returns:
            The crawler class (not instantiated)

        Raises:
            CrawlerNotFoundError: If module or class not found
        """
        # Check cache first
        if site_name in self._crawler_cache:
            return self._crawler_cache[site_name]

        # Build module path: src.plugins.forest_korea.crawler
        module_path = f"src.plugins.{site_name}.crawler"

        try:
            # Dynamically import the module
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise CrawlerNotFoundError(
                f"Plugin '{site_name}' not found at {module_path}. "
                f"Make sure the plugin directory exists at {self.plugins_dir / site_name}"
            ) from e

        # Find the crawler class (should end with 'Crawler')
        crawler_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type) and
                issubclass(attr, BaseCrawler) and
                attr is not BaseCrawler
            ):
                crawler_class = attr
                break

        if crawler_class is None:
            raise CrawlerNotFoundError(
                f"No BaseCrawler subclass found in {module_path}. "
                f"Make sure your crawler class inherits from BaseCrawler."
            )

        # Cache for future use
        self._crawler_cache[site_name] = crawler_class

        return crawler_class

    def list_available_plugins(self) -> list[str]:
        """
        List all available crawler plugins.

        Returns:
            List of plugin names (directory names under plugins_dir)

        Example:
            >>> factory = ParserFactory()
            >>> print(factory.list_available_plugins())
            ['forest_korea', 'naver_cafe', 'g2b']
        """
        if not self.plugins_dir.exists():
            return []

        plugins = []
        for item in self.plugins_dir.iterdir():
            # Check if it's a directory with __init__.py
            if item.is_dir() and (item / "__init__.py").exists():
                plugins.append(item.name)

        return sorted(plugins)

    def get_plugin_config(self, site_name: str) -> Optional[Dict[str, Any]]:
        """
        Load the config.yaml for a specific plugin.

        Args:
            site_name: Name of the plugin

        Returns:
            Parsed YAML config as a dict, or None if not found

        Example:
            >>> factory = ParserFactory()
            >>> config = factory.get_plugin_config('forest_korea')
            >>> print(config['site']['base_url'])
            https://www.forest.go.kr
        """
        config_path = self.plugins_dir / site_name / "config.yaml"

        if not config_path.exists():
            return None

        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_plugin_metadata(self, site_name: str) -> Dict[str, Any]:
        """
        Get metadata about a plugin (name, version, description, etc.).

        Args:
            site_name: Name of the plugin

        Returns:
            Dictionary with plugin metadata

        Example:
            >>> factory = ParserFactory()
            >>> meta = factory.get_plugin_metadata('forest_korea')
            >>> print(meta['display_name'])
            산림청 입찰정보
        """
        config = self.get_plugin_config(site_name)

        if config and 'plugin' in config:
            return config['plugin']

        # Default metadata if config not found
        return {
            'name': site_name,
            'display_name': site_name.replace('_', ' ').title(),
            'version': '1.0.0',
            'description': 'No description available'
        }


if __name__ == "__main__":
    # Test the factory
    print("=== ParserFactory Test ===\n")

    factory = ParserFactory()

    # Test listing plugins
    print("Available plugins:")
    plugins = factory.list_available_plugins()
    if plugins:
        for plugin in plugins:
            print(f"  - {plugin}")
    else:
        print("  (no plugins found - this is expected if plugins haven't been created yet)")

    print("\n✓ ParserFactory instantiated successfully")

    # Test error handling
    print("\nTesting error handling...")
    try:
        crawler = factory.create_crawler('nonexistent_plugin')
    except CrawlerNotFoundError as e:
        print(f"✓ Correctly raised CrawlerNotFoundError: {type(e).__name__}")

    print("\n✓ All tests passed")
