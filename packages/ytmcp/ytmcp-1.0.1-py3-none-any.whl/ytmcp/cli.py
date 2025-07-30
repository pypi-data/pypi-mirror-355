# ytmcp/cli.py
"""
Command line interface for ytmcp
"""

import argparse
import asyncio
import sys
from typing import List, Optional

from .server import YouTubeTranscriptMCPServer


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        prog="ytmcp",
        description="YouTube Transcript MCP Server",
        epilog="For more information, visit: https://github.com/yourusername/ytmcp"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.1"
    )
    
    parser.add_argument(
        "--stdio",
        action="store_true",
        default=True,
        help="Run in stdio mode (default)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a simple test to verify installation"
    )
    
    parser.add_argument(
        "--video-id",
        type=str,
        help="Test with specific video ID (requires --test)"
    )
    
    return parser


async def test_server(video_id: Optional[str] = None) -> bool:
    """Test the server functionality"""
    test_video = video_id or "dQw4w9WgXcQ"  # Rick Roll as default test
    
    print(f"Testing ytmcp server with video: {test_video}")
    
    try:
        server = YouTubeTranscriptMCPServer()
        
        # Test listing available transcripts
        print("Testing list_available_transcripts...")
        result = await server.list_available_transcripts({"video_url_or_id": test_video})
        print(f"✓ Found {result['total_transcripts']} transcripts")
        
        # Test getting transcript
        print("Testing get_transcript...")
        result = await server.get_transcript({
            "video_url_or_id": test_video,
            "languages": ["en"],
            "include_timestamps": True
        })
        print(f"✓ Retrieved transcript with {result['transcript_count']} segments")
        print(f"✓ Language: {result['language']} ({result['language_code']})")
        
        if result['transcript']:
            first_segment = result['transcript'][0]
            print(f"✓ First segment: '{first_segment['text'][:50]}...'")
            print(f"✓ Timestamp: {first_segment['start']:.1f}s - {first_segment['end']:.1f}s")
        
        print("\n✅ All tests passed! ytmcp is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point"""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.test:
        success = asyncio.run(test_server(parsed_args.video_id))
        return 0 if success else 1
    
    # Default: run in stdio mode
    print("Starting YouTube Transcript MCP Server...", file=sys.stderr)
    print("Ready to accept MCP requests via stdio", file=sys.stderr)
    
    try:
        server = YouTubeTranscriptMCPServer()
        asyncio.run(server.run_stdio())
        return 0
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
