"""Quick-TTS MCP Server implementation."""

import asyncio
import json
import sys
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent
)

from .tools import TTSTools


app = FastMCP("quick-tts-mcp")


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available TTS tools."""
    return [
        Tool(
            name="generate_speech",
            description="Convert text to speech using OpenAI's TTS API",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech"
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice to use",
                        "enum": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                        "default": "alloy"
                    },
                    "model": {
                        "type": "string", 
                        "description": "Model to use",
                        "enum": ["tts-1", "tts-1-hd"],
                        "default": "tts-1-hd"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output audio format",
                        "enum": ["mp3", "wav"],
                        "default": "mp3"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="list_voices",
            description="List available TTS voices",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_models", 
            description="List available TTS models",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "generate_speech":
            result = TTSTools.generate_speech(**arguments)
        elif name == "list_voices":
            result = TTSTools.list_voices()
        elif name == "list_models":
            result = TTSTools.list_models()
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


def main():
    """Main entry point for the MCP server."""
    app.run()


if __name__ == "__main__":
    main()
