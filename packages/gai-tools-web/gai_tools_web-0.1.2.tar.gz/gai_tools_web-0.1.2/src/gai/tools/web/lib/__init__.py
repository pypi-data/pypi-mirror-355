# web/lib/__init__.py

from .dtos import (
    ScrapeRequest,
    ParsedChunk,
    ParsedResponse,
    SearchRequest,
    SearchResponse,
    CrawlTreeNode,
    CrawlJob,
    CrawlRequest,
    UrlRequest,
)

__all__ = [
    "ScrapeRequest",
    "ParsedChunk",
    "ParsedResponse",
    "SearchRequest",
    "SearchResponse",
    "CrawlTreeNode",
    "CrawlJob",
    "CrawlRequest",
    "UrlRequest",
]