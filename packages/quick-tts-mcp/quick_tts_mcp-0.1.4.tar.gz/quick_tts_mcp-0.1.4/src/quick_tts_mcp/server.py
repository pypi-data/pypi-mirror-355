"""Quick-TTS MCP Server implementation."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

try:
    from .tools import TTSTools
except ImportError:
    from quick_tts_mcp.tools import TTSTools


mcp = FastMCP("quick-tts-mcp")


@mcp.tool()
def generate_speech(
    text: str,
    voice: str = "alloy",
    model: str = "tts-1-hd",
    output_format: str = "mp3",
    output_path: str = None,
    use_temp_dir: bool = False
) -> str:
    """Convert text to speech using OpenAI's TTS API.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        model: Model to use (tts-1, tts-1-hd)
        output_format: Output audio format (mp3, wav)
        output_path: Optional custom output file path
        use_temp_dir: If True, save to temp directory (default: save to current directory)
    
    Returns:
        JSON string with file path and metadata
    """
    result = TTSTools.generate_speech(text, voice, model, output_format, output_path, use_temp_dir)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_voices() -> str:
    """List available TTS voices.
    
    Returns:
        JSON string with available voices and descriptions
    """
    result = TTSTools.list_voices()
    return json.dumps(result, indent=2)


@mcp.tool()
def list_models() -> str:
    """List available TTS models.
    
    Returns:
        JSON string with available models and descriptions
    """
    result = TTSTools.list_models()
    return json.dumps(result, indent=2)


def main():
    """Main entry point for the MCP server."""
    print("🎤 Quick-TTS MCP Server v0.1.4 starting...")
    print("Ready to convert text to speech using OpenAI's TTS API!")
    mcp.run()


if __name__ == "__main__":
    main()
