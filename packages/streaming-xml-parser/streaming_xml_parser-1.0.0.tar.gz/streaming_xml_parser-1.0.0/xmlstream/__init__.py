"""
Streaming XML Parser

A high-performance, configurable streaming XML parser designed for real-time processing
of XML content in streaming applications. Supports different behavior types for different
XML tags, enabling both immediate streaming output and placeholder status messages.

Author: Assistant
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Assistant"
__description__ = "High-performance streaming XML parser for real-time applications"

# Core exports
from .core import StreamingXMLParser
from .events import StreamingEvent, EventType
from .config import TagConfig, TagState
from .behaviors import TagBehavior
from .handlers import StreamingOutputHandler, CollectingOutputHandler, CallbackOutputHandler
from .exceptions import (
    StreamingXMLError, 
    TagNotFoundError, 
    InvalidTagError,
    ConfigurationError,
    BufferOverflowError
)

__all__ = [
    # Core classes
    "StreamingXMLParser",
    "StreamingEvent",
    "EventType",
    "TagConfig",
    "TagState",
    "TagBehavior",
    "StreamingOutputHandler",
    "CollectingOutputHandler",
    "CallbackOutputHandler",
    # Exceptions
    "StreamingXMLError",
    "TagNotFoundError", 
    "InvalidTagError",
    "ConfigurationError",
    "BufferOverflowError",
    # Package info
    "__version__",
    "__author__",
    "__description__",
] 