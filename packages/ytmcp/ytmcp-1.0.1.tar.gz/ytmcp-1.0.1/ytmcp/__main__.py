# ytmcp/__main__.py
"""
Entry point for running ytmcp as a module: python -m ytmcp
"""

import asyncio
from .server import YouTubeTranscriptMCPServer


def main():
    """Main entry point for module execution"""
    server = YouTubeTranscriptMCPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()