"""
Event system for the streaming XML parser.

This module defines the event classes and types used by the parser
to communicate parsing progress and results.
"""

from typing import Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamingEvent:
    """
    Represents an event emitted by the streaming parser.
    
    This class uses dataclass with frozen=True for immutability and
    better performance compared to the original implementation.
    
    Attributes:
        event_type: The type of event (content, tag_start, tag_content, tag_complete)
        tag_name: Name of the tag associated with this event (optional)
        content: Content data for the event (optional)
        data: Additional data payload (optional)
    """
    event_type: str
    tag_name: Optional[str] = None
    content: Optional[str] = None
    data: Optional[Any] = None
    
    def __post_init__(self):
        """Validate event data after initialization."""
        valid_types = {"content", "tag_start", "tag_content", "tag_complete"}
        if self.event_type not in valid_types:
            raise ValueError(f"Invalid event_type: {self.event_type}. Must be one of {valid_types}")
    
    def is_content_event(self) -> bool:
        """Check if this is a content-related event."""
        return self.event_type in {"content", "tag_content"}
    
    def is_tag_event(self) -> bool:
        """Check if this is a tag-related event."""
        return self.event_type in {"tag_start", "tag_complete"}
    
    def has_content(self) -> bool:
        """Check if this event contains content data."""
        return self.content is not None and len(self.content) > 0


class EventType:
    """
    Constants for event types to avoid string literals throughout the code.
    
    This provides type safety and makes refactoring easier.
    """
    CONTENT = "content"
    TAG_START = "tag_start"
    TAG_CONTENT = "tag_content"
    TAG_COMPLETE = "tag_complete"
    
    @classmethod
    def all_types(cls) -> set[str]:
        """Return all valid event types."""
        return {cls.CONTENT, cls.TAG_START, cls.TAG_CONTENT, cls.TAG_COMPLETE} 