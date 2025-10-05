"""
Core module for universal board crawler.

This module contains the base abstractions and utilities that all
site-specific plugins must use.
"""

from .base_crawler import BaseCrawler
from .parser_factory import ParserFactory, CrawlerNotFoundError

__all__ = ['BaseCrawler', 'ParserFactory', 'CrawlerNotFoundError']
