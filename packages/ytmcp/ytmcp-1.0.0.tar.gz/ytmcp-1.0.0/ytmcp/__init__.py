
# ytmcp/__init__.py
"""
YTMcp - YouTube Transcript MCP Server

A Model Context Protocol server for fetching YouTube transcripts with timestamps.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

from .server import YouTubeTranscriptMCPServer

__all__ = ["YouTubeTranscriptMCPServer"]
