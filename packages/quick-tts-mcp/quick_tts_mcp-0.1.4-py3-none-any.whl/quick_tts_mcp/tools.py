"""TTS tools for the MCP server."""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict
import hashlib

from quick_tts import text_to_speech


class TTSTools:
    """Text-to-speech tools for MCP server."""
    
    @staticmethod
    def generate_speech(
        text: str,
        voice: str = "alloy",
        model: str = "tts-1-hd",
        output_format: str = "mp3",
        output_path: str = None,
        use_temp_dir: bool = False
    ) -> Dict[str, Any]:
        """
        Generate speech from text using OpenAI's TTS API.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: Model to use (tts-1, tts-1-hd)
            output_format: Output format (mp3, wav, etc.)
            output_path: Optional custom output file path
            use_temp_dir: If True, save to temp directory instead of current directory
            
        Returns:
            Dictionary with file path and metadata
        """
        try:
            if output_path:
                # Use custom path, ensure correct extension
                if not output_path.endswith(f".{output_format}"):
                    output_path = f"{output_path}.{output_format}"
                final_output_path = output_path
            elif use_temp_dir:
                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=f".{output_format}", 
                    delete=False
                ) as tmp_file:
                    final_output_path = tmp_file.name
            else:
                # Default: save to current working directory with meaningful name
                # Create filename based on text hash to avoid duplicates
                text_hash = hashlib.md5(f"{text}_{voice}_{model}".encode()).hexdigest()[:8]
                filename = f"speech_{text_hash}_{voice}.{output_format}"
                final_output_path = os.path.join(os.getcwd(), filename)
            
            # Generate speech
            result_path = text_to_speech(
                text=text,
                output_file=final_output_path,
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
