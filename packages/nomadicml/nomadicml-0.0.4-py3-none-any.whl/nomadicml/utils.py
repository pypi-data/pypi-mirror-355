"""Utility functions for the NomadicML SDK."""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from .exceptions import ValidationError
from .types import VideoSource

logger = logging.getLogger("nomadicml")


def validate_api_key(api_key: str) -> None:
    """
    Validate the format of an API key.
    
    Args:
        api_key: The API key to validate.
        
    Raises:
        ValidationError: If the API key format is invalid.
    """
    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string")
    
    if not api_key.strip():
        raise ValidationError("API key cannot be empty")


def infer_source(file_path: str) -> VideoSource:
    """Infer the :class:`~nomadicml.types.VideoSource` for *file_path*.

    The heuristic is:

    • If *file_path* exists locally and is a regular file ⇒ ``VideoSource.FILE``.
    • Else, if it looks like a valid URL ⇒ ``VideoSource.VIDEO_URL``.
    • Otherwise, raise :class:`ValidationError`.
    """
    if not isinstance(file_path, str):
        raise ValidationError("file_path must be a string")

    # First assume local file if it clearly exists
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return VideoSource.FILE

    # Otherwise treat as URL (and validate syntax)
    parsed = urlparse(file_path)
    if parsed.scheme and parsed.netloc:
        return VideoSource.VIDEO_URL

    raise ValidationError(
        "file_path must be either an existing local file or a valid URL (http://, https://, s3://, …)"
    )

def format_error_message(response_data: Dict[str, Any]) -> str:
    """
    Format an error message from the API response.
    
    Args:
        response_data: The response data from the API.
        
    Returns:
        A formatted error message.
    """
    if isinstance(response_data, dict):
        # Try to extract error message from common patterns
        if "detail" in response_data:
            detail = response_data["detail"]
            if isinstance(detail, list):
                # Handle validation errors which are often lists
                return "; ".join(f"{err.get('loc', [''])[0]}: {err.get('msg', '')}" 
                                for err in detail)
            return str(detail)
        elif "message" in response_data:
            return str(response_data["message"])
        elif "error" in response_data:
            return str(response_data["error"])
    
    # Fallback to returning the entire response as a string
    return str(response_data)


def get_file_mime_type(file_path: str) -> str:
    """
    Get the MIME type of a file based on its extension.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        The MIME type of the file.
    """
    _, ext = os.path.splitext(file_path)
    
    # Simple mapping of common file extensions to MIME types
    mime_types = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".wmv": "video/x-ms-wmv",
        ".flv": "video/x-flv",
        ".mkv": "video/x-matroska",
    }
    
    return mime_types.get(ext.lower(), "application/octet-stream")


def get_filename_from_path(file_path: str) -> str:
    """
    Extract the filename from a file path.
    
    Args:
        file_path: The file path.
        
    Returns:
        The filename.
    """
    return os.path.basename(file_path)
