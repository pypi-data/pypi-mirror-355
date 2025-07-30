"""
YouTube Transcript MCP Server

Provides YouTube transcript fetching capabilities via the Model Context Protocol.
"""

import asyncio
import json
import sys
import re
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

# Import from the bundled youtube_transcript_api
try:
    from .youtube_transcript_api import YouTubeTranscriptApi
    from .youtube_transcript_api._errors import (
        YouTubeTranscriptApiException,
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
        RequestBlocked,
        InvalidVideoId
    )
except ImportError:
    # Fallback to external package if bundled version not found
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            YouTubeTranscriptApiException,
            NoTranscriptFound,
            TranscriptsDisabled,
            VideoUnavailable,
            RequestBlocked,
            InvalidVideoId
        )
    except ImportError as e:
        raise ImportError(
            "youtube-transcript-api is required but not found. "
            "This should be bundled with ytmcp. Please reinstall ytmcp."
        ) from e


@dataclass
class MCPRequest:
    """MCP request structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    """MCP response structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class YouTubeTranscriptMCPServer:
    """
    YouTube Transcript MCP Server
    
    Provides YouTube transcript fetching capabilities through the Model Context Protocol.
    Supports multiple languages, time-range filtering, and comprehensive error handling.
    """
    
    def __init__(self):
        """Initialize the MCP server"""
        self.name = "ytmcp"
        self.version = "1.0.0"
        self.api = YouTubeTranscriptApi()
        
    def extract_video_id(self, url_or_id: str) -> str:
        """
        Extract video ID from YouTube URL or return ID if already provided
        
        Args:
            url_or_id: YouTube URL or video ID
            
        Returns:
            Extracted video ID
            
        Raises:
            ValueError: If video ID cannot be extracted
        """
        # If it's already a video ID (11 characters, alphanumeric and dashes/underscores)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
            
        # Extract from various YouTube URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
                
        # If no pattern matches but it might still be a video ID, try it
        if len(url_or_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url_or_id):
            return url_or_id
            
        raise ValueError(f"Could not extract video ID from: {url_or_id}")

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Main request handler for MCP protocol
        
        Args:
            request: MCP request object
            
        Returns:
            MCP response object
        """
        # Ensure we always have a valid response structure
        response = MCPResponse(id=request.id)
        
        try:
            if request.method == "initialize":
                response.result = await self.initialize(request.params or {})
            elif request.method == "tools/list":
                response.result = await self.list_tools()
            elif request.method == "tools/call":
                response.result = await self.call_tool(request.params or {})
            elif request.method == "resources/list":
                response.result = {"resources": []}  # No static resources
            elif request.method == "prompts/list":
                response.result = {"prompts": []}  # No prompts
            else:
                response.error = {
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
        except Exception as e:
            response.error = {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
            
        return response

    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the MCP server"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": "get_transcript",
                    "description": "Fetch transcript for a YouTube video with timestamps",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "video_url_or_id": {
                                "type": "string",
                                "description": "YouTube video URL or video ID"
                            },
                            "languages": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preferred languages in priority order (e.g., ['en', 'es'])",
                                "default": ["en"]
                            },
                            "preserve_formatting": {
                                "type": "boolean",
                                "description": "Whether to preserve HTML formatting in transcript text",
                                "default": False
                            },
                            "include_timestamps": {
                                "type": "boolean", 
                                "description": "Whether to include start and end timestamps",
                                "default": True
                            }
                        },
                        "required": ["video_url_or_id"]
                    }
                },
                {
                    "name": "list_available_transcripts",
                    "description": "List all available transcript languages for a YouTube video",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "video_url_or_id": {
                                "type": "string",
                                "description": "YouTube video URL or video ID"
                            }
                        },
                        "required": ["video_url_or_id"]
                    }
                },
                {
                    "name": "get_transcript_with_time_range", 
                    "description": "Fetch transcript for a specific time range of a YouTube video",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "video_url_or_id": {
                                "type": "string",
                                "description": "YouTube video URL or video ID"
                            },
                            "start_time": {
                                "type": "number",
                                "description": "Start time in seconds"
                            },
                            "end_time": {
                                "type": "number", 
                                "description": "End time in seconds"
                            },
                            "languages": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preferred languages in priority order",
                                "default": ["en"]
                            },
                            "preserve_formatting": {
                                "type": "boolean",
                                "description": "Whether to preserve HTML formatting",
                                "default": False
                            }
                        },
                        "required": ["video_url_or_id", "start_time", "end_time"]
                    }
                }
            ]
        }

    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if name == "get_transcript":
                result = await self.get_transcript(arguments)
            elif name == "list_available_transcripts":
                result = await self.list_available_transcripts(arguments)
            elif name == "get_transcript_with_time_range":
                result = await self.get_transcript_with_time_range(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Error: {str(e)}"
                    }
                ]
            }

    async def get_transcript(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch transcript for a YouTube video
        
        Args:
            args: Dictionary containing video_url_or_id, languages, preserve_formatting, include_timestamps
            
        Returns:
            Dictionary with transcript data and metadata
        """
        video_url_or_id = args["video_url_or_id"]
        languages = args.get("languages", ["en"])
        preserve_formatting = args.get("preserve_formatting", False)
        include_timestamps = args.get("include_timestamps", True)
        
        try:
            video_id = self.extract_video_id(video_url_or_id)
            
            # Fetch the transcript
            transcript = self.api.fetch(
                video_id=video_id,
                languages=languages,
                preserve_formatting=preserve_formatting
            )
            
            # Format the response
            result = {
                "video_id": transcript.video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "transcript_count": len(transcript.snippets)
            }
            
            if include_timestamps:
                result["transcript"] = [
                    {
                        "text": snippet.text,
                        "start": snippet.start,
                        "duration": snippet.duration,
                        "end": snippet.start + snippet.duration
                    }
                    for snippet in transcript.snippets
                ]
            else:
                result["full_text"] = "\n".join(snippet.text for snippet in transcript.snippets)
                
            return result
            
        except InvalidVideoId:
            raise ValueError(f"Invalid video ID or URL: {video_url_or_id}")
        except NoTranscriptFound:
            raise ValueError(f"No transcript found for languages: {languages}")
        except TranscriptsDisabled:
            raise ValueError("Transcripts are disabled for this video")
        except VideoUnavailable:
            raise ValueError("Video is unavailable")
        except RequestBlocked:
            raise ValueError("Request blocked by YouTube - consider using a proxy")
        except YouTubeTranscriptApiException as e:
            raise ValueError(f"YouTube API error: {str(e)}")

    async def list_available_transcripts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all available transcript languages for a video
        
        Args:
            args: Dictionary containing video_url_or_id
            
        Returns:
            Dictionary with available transcript information
        """
        video_url_or_id = args["video_url_or_id"]
        
        try:
            video_id = self.extract_video_id(video_url_or_id)
            
            # Get transcript list
            transcript_list = self.api.list(video_id)
            
            manually_created = []
            auto_generated = []
            
            for transcript in transcript_list:
                transcript_info = {
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_translatable": transcript.is_translatable
                }
                
                if transcript.is_generated:
                    auto_generated.append(transcript_info)
                else:
                    manually_created.append(transcript_info)
            
            return {
                "video_id": video_id,
                "manually_created_transcripts": manually_created,
                "auto_generated_transcripts": auto_generated,
                "total_transcripts": len(manually_created) + len(auto_generated)
            }
            
        except InvalidVideoId:
            raise ValueError(f"Invalid video ID or URL: {video_url_or_id}")
        except TranscriptsDisabled:
            raise ValueError("Transcripts are disabled for this video")
        except VideoUnavailable:
            raise ValueError("Video is unavailable")
        except YouTubeTranscriptApiException as e:
            raise ValueError(f"YouTube API error: {str(e)}")

    async def get_transcript_with_time_range(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch transcript for a specific time range
        
        Args:
            args: Dictionary containing video_url_or_id, start_time, end_time, languages, preserve_formatting
            
        Returns:
            Dictionary with filtered transcript data
        """
        video_url_or_id = args["video_url_or_id"]
        start_time = float(args["start_time"])
        end_time = float(args["end_time"])
        languages = args.get("languages", ["en"])
        preserve_formatting = args.get("preserve_formatting", False)
        
        if start_time >= end_time:
            raise ValueError("start_time must be less than end_time")
            
        try:
            video_id = self.extract_video_id(video_url_or_id)
            
            # Fetch the full transcript
            transcript = self.api.fetch(
                video_id=video_id,
                languages=languages,
                preserve_formatting=preserve_formatting
            )
            
            # Filter snippets within the time range
            filtered_snippets = []
            for snippet in transcript.snippets:
                snippet_end = snippet.start + snippet.duration
                
                # Include snippet if it overlaps with the requested time range
                if snippet.start < end_time and snippet_end > start_time:
                    filtered_snippets.append({
                        "text": snippet.text,
                        "start": snippet.start,
                        "duration": snippet.duration,
                        "end": snippet_end
                    })
            
            return {
                "video_id": transcript.video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "time_range": {
                    "start": start_time,
                    "end": end_time
                },
                "filtered_transcript": filtered_snippets,
                "snippet_count": len(filtered_snippets)
            }
            
        except YouTubeTranscriptApiException as e:
            raise ValueError(f"YouTube API error: {str(e)}")

    def _format_response(self, response: MCPResponse) -> Dict[str, Any]:
        """Format response for JSON-RPC compliance"""
        response_data = {
            "jsonrpc": response.jsonrpc,
        }
        
        # Handle ID properly - never send undefined/null for responses with content
        if response.id is not None:
            response_data["id"] = response.id
        else:
            # For responses that need an ID but don't have one, use a default
            response_data["id"] = 0
        
        # Either result or error, never both
        if response.error is not None:
            response_data["error"] = response.error
        else:
            response_data["result"] = response.result or {}
            
        return response_data

    async def run_stdio(self):
        """Run the server using stdio transport"""
        # Send startup message to stderr so it doesn't interfere with JSON-RPC
        print("Starting YouTube Transcript MCP Server...", file=sys.stderr)
        print("Ready to accept MCP requests via stdio", file=sys.stderr)
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    request_data = json.loads(line)
                except json.JSONDecodeError as e:
                    # Send parse error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                
                # Build request object with proper defaults
                request = MCPRequest(
                    jsonrpc=request_data.get("jsonrpc", "2.0"),
                    id=request_data.get("id"),
                    method=request_data.get("method", ""),
                    params=request_data.get("params")
                )
                
                # Handle the request
                response = await self.handle_request(request)
                
                # Format and send response
                response_data = self._format_response(response)
                print(json.dumps(response_data), flush=True)
                
            except KeyboardInterrupt:
                print("Shutting down server...", file=sys.stderr)
                break
            except Exception as e:
                # Send generic error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)