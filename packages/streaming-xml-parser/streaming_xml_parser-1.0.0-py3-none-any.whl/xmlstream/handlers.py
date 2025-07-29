"""
Output handlers for the streaming XML parser.

This module provides various output handlers that can be used to process
and display the results of XML parsing in different ways.
"""

from typing import Callable, Dict, Any, Optional, Protocol
import sys

from .events import StreamingEvent, EventType
from .behaviors import TagBehavior


class OutputWriter(Protocol):
    """Protocol for output writers."""
    
    def write(self, text: str) -> None:
        """Write text to the output."""
        ...
    
    def flush(self) -> None:
        """Flush the output buffer."""
        ...


class StreamingOutputHandler:
    """
    Handles the output of streaming events with different behaviors.
    
    This class demonstrates how to use the StreamingXMLParser for real applications
    and provides a flexible way to handle different types of events.
    """
    
    def __init__(self, 
                 output_writer: Optional[OutputWriter] = None,
                 placeholder_prefix: str = "\n",
                 placeholder_suffix: str = " ✓\n",
                 enable_colors: bool = True):
        """
        Initialize the output handler.
        
        Args:
            output_writer: Writer for outputting text (default: sys.stdout)
            placeholder_prefix: Prefix for placeholder messages
            placeholder_suffix: Suffix for completed placeholder messages
            enable_colors: Whether to enable color output (future feature)
        """
        self.output_writer = output_writer or sys.stdout
        self.placeholder_prefix = placeholder_prefix
        self.placeholder_suffix = placeholder_suffix
        self.enable_colors = enable_colors
        self.active_placeholders: Dict[str, bool] = {}
        
    def handle_event(self, event: StreamingEvent) -> None:
        """
        Handle a streaming event based on its type and tag behavior.
        
        Args:
            event: The streaming event to handle
        """
        if event.event_type == EventType.CONTENT:
            self._handle_content(event)
        elif event.event_type == EventType.TAG_START:
            self._handle_tag_start(event)
        elif event.event_type == EventType.TAG_CONTENT:
            self._handle_tag_content(event)
        elif event.event_type == EventType.TAG_COMPLETE:
            self._handle_tag_complete(event)
    
    def _handle_content(self, event: StreamingEvent) -> None:
        """Handle regular content outside tags."""
        if event.content:
            self._write(event.content)
    
    def _handle_tag_start(self, event: StreamingEvent) -> None:
        """Handle tag start events."""
        if not event.data or not hasattr(event.data, 'behavior'):
            return
            
        config = event.data
        if (config.behavior == TagBehavior.PLACEHOLDER and 
            hasattr(config, 'placeholder_message') and 
            config.placeholder_message):
            self._write(f"{self.placeholder_prefix}{config.placeholder_message}")
            self.active_placeholders[event.tag_name] = True
    
    def _handle_tag_content(self, event: StreamingEvent) -> None:
        """Handle tag content events."""
        if not event.data or not hasattr(event.data, 'behavior'):
            return
            
        config = event.data
        if config.behavior == TagBehavior.STREAMING and event.content:
            self._write(event.content)
    
    def _handle_tag_complete(self, event: StreamingEvent) -> None:
        """Handle tag completion events."""
        if not event.data or not hasattr(event.data, 'behavior'):
            return
            
        config = event.data
        if config.behavior == TagBehavior.PLACEHOLDER:
            if event.tag_name in self.active_placeholders:
                self._write(self.placeholder_suffix)
                del self.active_placeholders[event.tag_name]
    
    def _write(self, text: str) -> None:
        """Write text to the output writer."""
        self.output_writer.write(text)
        if hasattr(self.output_writer, 'flush'):
            self.output_writer.flush()
    
    def reset(self) -> None:
        """Reset the handler state."""
        self.active_placeholders.clear()


class CollectingOutputHandler:
    """
    An output handler that collects all output into a buffer.
    
    This is useful for testing or when you want to process the complete
    output after parsing is finished.
    """
    
    def __init__(self):
        """Initialize the collecting handler."""
        self.buffer: list[str] = []
        self.events: list[StreamingEvent] = []
    
    def handle_event(self, event: StreamingEvent) -> None:
        """
        Collect events and their content.
        
        Args:
            event: The streaming event to collect
        """
        self.events.append(event)
        
        if event.has_content():
            self.buffer.append(event.content)
    
    def get_content(self) -> str:
        """Get all collected content as a single string."""
        return ''.join(self.buffer)
    
    def get_events(self) -> list[StreamingEvent]:
        """Get all collected events."""
        return self.events.copy()
    
    def clear(self) -> None:
        """Clear all collected data."""
        self.buffer.clear()
        self.events.clear()


class CallbackOutputHandler:
    """
    An output handler that calls custom callbacks for different event types.
    
    This provides maximum flexibility for custom processing of streaming events.
    """
    
    def __init__(self, 
                 on_content: Optional[Callable[[str], None]] = None,
                 on_tag_start: Optional[Callable[[str, Any], None]] = None,
                 on_tag_content: Optional[Callable[[str, str, Any], None]] = None,
                 on_tag_complete: Optional[Callable[[str, str, Any], None]] = None):
        """
        Initialize the callback handler.
        
        Args:
            on_content: Callback for content events
            on_tag_start: Callback for tag start events
            on_tag_content: Callback for tag content events
            on_tag_complete: Callback for tag complete events
        """
        self.on_content = on_content
        self.on_tag_start = on_tag_start
        self.on_tag_content = on_tag_content
        self.on_tag_complete = on_tag_complete
    
    def handle_event(self, event: StreamingEvent) -> None:
        """
        Handle events by calling appropriate callbacks.
        
        Args:
            event: The streaming event to handle
        """
        if event.event_type == EventType.CONTENT and self.on_content:
            self.on_content(event.content or "")
        elif event.event_type == EventType.TAG_START and self.on_tag_start:
            self.on_tag_start(event.tag_name or "", event.data)
        elif event.event_type == EventType.TAG_CONTENT and self.on_tag_content:
            self.on_tag_content(event.tag_name or "", event.content or "", event.data)
        elif event.event_type == EventType.TAG_COMPLETE and self.on_tag_complete:
            self.on_tag_complete(event.tag_name or "", event.content or "", event.data) 