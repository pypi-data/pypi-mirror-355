"""TTS tools for the MCP server."""

import tempfile
from pathlib import Path
from typing import Any, Dict

from quick_tts import text_to_speech


class TTSTools:
    """Text-to-speech tools for MCP server."""
    
    @staticmethod
    def generate_speech(
        text: str,
        voice: str = "alloy",
        model: str = "tts-1-hd",
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Generate speech from text using OpenAI's TTS API.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: Model to use (tts-1, tts-1-hd)
            output_format: Output format (mp3, wav, etc.)
            
        Returns:
            Dictionary with file path and metadata
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{output_format}", 
                delete=False
            ) as tmp_file:
                output_path = tmp_file.name
            
            # Generate speech
            result_path = text_to_speech(
                text=text,
                output_file=output_path,
                model=model,
                voice=voice
            )
            
            # Get file size
            file_size = Path(result_path).stat().st_size
            
            return {
                "success": True,
                "file_path": result_path,
                "file_size": file_size,
                "text": text,
                "voice": voice,
                "model": model,
                "format": output_format
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def list_voices() -> Dict[str, Any]:
        """List available voices."""
        return {
            "voices": [
                {"name": "alloy", "description": "Balanced, versatile voice"},
                {"name": "echo", "description": "Clear, professional tone"},
                {"name": "fable", "description": "Warm, storytelling quality"},
                {"name": "onyx", "description": "Deep, authoritative voice"},
                {"name": "nova", "description": "Bright, engaging tone"},
                {"name": "shimmer", "description": "Soft, pleasant voice"}
            ]
        }
    
    @staticmethod
    def list_models() -> Dict[str, Any]:
        """List available models."""
        return {
            "models": [
                {"name": "tts-1", "description": "Standard quality, faster generation"},
                {"name": "tts-1-hd", "description": "High definition quality, more detailed audio"}
            ]
        }
