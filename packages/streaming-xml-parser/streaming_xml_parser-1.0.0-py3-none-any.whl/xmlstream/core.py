"""
Core streaming XML parser implementation.

This module contains the main StreamingXMLParser class that handles
the actual parsing logic with optimized performance and robust error handling.
"""

from typing import Dict, Generator, Optional, List
import logging

from .events import StreamingEvent, EventType
from .config import TagConfig, TagState
from .behaviors import TagBehavior
from .exceptions import TagNotFoundError, InvalidTagError, BufferOverflowError

logger = logging.getLogger(__name__)


class StreamingXMLParser:
    """
    High-performance streaming XML parser with stack-based nesting support.
    
    Features:
    - Real-time streaming output for designated tags
    - Placeholder status messages for background operations
    - Stack-based nesting with simplified rules:
      * Streaming tags block nesting (nested tags become content)
      * Non-streaming tags allow proper nesting
    - Efficient buffer management with optimizations
    - Event-driven architecture
    - Production-ready error handling
    """
    
    # Buffer safety limits
    DEFAULT_MAX_BUFFER_SIZE = 1024 * 1024  # 1MB default limit
    
    def __init__(self, 
                 tag_configs: Dict[str, TagConfig],
                 max_buffer_size: int = DEFAULT_MAX_BUFFER_SIZE):
        """
        Initialize the streaming XML parser.
        
        Args:
            tag_configs: Dictionary mapping tag names to their configurations
            max_buffer_size: Maximum allowed buffer size for safety
        """
        self.tag_configs = tag_configs
        self.max_buffer_size = max_buffer_size
        self.reset()
        
        # Validate configurations
        self._validate_configs()
        
    def reset(self) -> None:
        """Reset parser state for reuse."""
        self.buffer = ""
        self.tag_stack: List[TagState] = []
        
    def add_tag_config(self, config: TagConfig) -> None:
        """
        Add or update a tag configuration.
        
        Args:
            config: The tag configuration to add
        """
        config.validate_callbacks()  # Validate before adding
        self.tag_configs[config.name] = config
        
    def remove_tag_config(self, tag_name: str) -> bool:
        """
        Remove a tag configuration.
        
        Args:
            tag_name: The name of the tag to remove
            
        Returns:
            bool: True if the tag was removed, False if it didn't exist
        """
        return self.tag_configs.pop(tag_name, None) is not None
        
    def is_streaming_mode(self) -> bool:
        """Check if we're currently in streaming mode (which blocks nesting)."""
        return (self.tag_stack and 
                self.tag_stack[-1].config.behavior == TagBehavior.STREAMING)
    
    def current_tag(self) -> Optional[TagState]:
        """Get the current (top) tag from the stack."""
        return self.tag_stack[-1] if self.tag_stack else None
        
    def process_chunk(self, chunk: str) -> Generator[StreamingEvent, None, None]:
        """
        Process a streaming chunk and yield events.
        
        Args:
            chunk: The incoming text chunk to process
            
        Yields:
            StreamingEvent: Events for tag starts, content, and completions
            
        Raises:
            BufferOverflowError: If buffer exceeds safety limits
        """
        if not chunk:
            return
            
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Processing chunk: {repr(chunk)}, stack depth: {len(self.tag_stack)}")
            
        self.buffer += chunk
        
        # Safety check for buffer size
        if len(self.buffer) > self.max_buffer_size:
            raise BufferOverflowError(len(self.buffer), self.max_buffer_size)
        
        while self.buffer:
            initial_buffer_len = len(self.buffer)
            
            if self.is_streaming_mode():
                # In streaming mode: only look for closing tag, everything else is content
                yield from self._process_streaming_mode()
            else:
                # Not in streaming mode: parse tags normally
                yield from self._process_normal_mode()
                
            # Prevent infinite loop - if buffer didn't change, break
            if len(self.buffer) == initial_buffer_len:
                break
                
    def _process_streaming_mode(self) -> Generator[StreamingEvent, None, None]:
        """Process content when in streaming mode (nested tags become content)."""
        current_tag = self.current_tag()
        if not current_tag:
            return
            
        closing_tag = f'</{current_tag.name}>'
        closing_idx = self.buffer.find(closing_tag)
        
        if closing_idx != -1:
            # Found closing tag - emit any remaining content and close tag
            if closing_idx > 0:
                content_chunk = self.buffer[:closing_idx]
                current_tag.add_content(content_chunk)
                yield StreamingEvent(
                    event_type=EventType.TAG_CONTENT,
                    tag_name=current_tag.name,
                    content=content_chunk,
                    data=current_tag.config
                )
            
            # Remove closing tag from buffer and close the tag
            self.buffer = self.buffer[closing_idx + len(closing_tag):]
            yield StreamingEvent(
                event_type=EventType.TAG_COMPLETE,
                tag_name=current_tag.name,
                content=current_tag.content,
                data=current_tag.config
            )
            self._close_current_tag()
            
        else:
            # No closing tag yet - stream available content but keep buffer for closing tag detection
            closing_tag_len = len(closing_tag)
            
            if len(self.buffer) >= closing_tag_len:
                # Keep enough characters for potential closing tag
                chars_to_keep = closing_tag_len - 1
                content_chunk = self.buffer[:-chars_to_keep] if chars_to_keep > 0 else self.buffer
                
                if content_chunk:
                    current_tag.add_content(content_chunk)
                    self.buffer = self.buffer[-chars_to_keep:] if chars_to_keep > 0 else ""
                    yield StreamingEvent(
                        event_type=EventType.TAG_CONTENT,
                        tag_name=current_tag.name,
                        content=content_chunk,
                        data=current_tag.config
                    )
            # If buffer is too short, wait for more content
                
    def _process_normal_mode(self) -> Generator[StreamingEvent, None, None]:
        """Process content when not in streaming mode (parse tags normally)."""
        # Optimized: Single-pass scan for both opening and closing tags
        earliest_start = -1
        best_tag_name = None
        best_tag_len = 0
        earliest_close = -1
        close_tag_name = None
        close_tag_len = 0
        
        # Single scan through buffer to find earliest opening or closing tag
        i = 0
        while i < len(self.buffer):
            if self.buffer[i] == '<':
                # Check for closing tags first (if we have active tags)
                if i + 1 < len(self.buffer) and self.buffer[i + 1] == '/' and self.tag_stack:
                    # Check for closing tags in reverse stack order (most recent first)
                    for tag_state in reversed(self.tag_stack):
                        closing_tag = f'</{tag_state.name}>'
                        if self.buffer[i:].startswith(closing_tag):
                            if earliest_close == -1 or i < earliest_close:
                                earliest_close = i
                                close_tag_name = tag_state.name
                                close_tag_len = len(closing_tag)
                            break  # Take the first (innermost) closing tag found
                
                # Check for opening tags
                else:
                    for tag_name in self.tag_configs.keys():
                        tag_start = f'<{tag_name}'
                        if self.buffer[i:].startswith(tag_start):
                            # Find the end of the opening tag (could have attributes)
                            tag_end_pos = self.buffer.find('>', i)
                            if tag_end_pos != -1:
                                # Verify this is actually our tag (not a substring of another tag)
                                tag_content = self.buffer[i:tag_end_pos + 1]
                                # Check if it's a valid opening tag (not self-closing)
                                if not tag_content.endswith('/>') and (earliest_start == -1 or i < earliest_start):
                                    earliest_start = i
                                    best_tag_name = tag_name
                                    best_tag_len = tag_end_pos - i + 1
                            break  # Found a match, no need to check other tags at this position
            i += 1
        
        # Determine what to process first: opening tag, closing tag, or content
        if earliest_start != -1 and (earliest_close == -1 or earliest_start < earliest_close):
            # Process opening tag
            if earliest_start > 0:
                # Yield content before the tag
                content = self.buffer[:earliest_start]
                if self.tag_stack:
                    # Add to current tag's content
                    current_tag = self.current_tag()
                    current_tag.add_content(content)
                    # Only emit content event if current tag is not silent
                    if current_tag.config.behavior != TagBehavior.SILENT:
                        yield StreamingEvent(
                            event_type=EventType.TAG_CONTENT,
                            tag_name=current_tag.name,
                            content=content,
                            data=current_tag.config
                        )
                else:
                    # No tags on stack, this is regular content
                    yield StreamingEvent(event_type=EventType.CONTENT, content=content)
            
            # Start processing the new tag
            self.buffer = self.buffer[earliest_start + best_tag_len:]
            yield from self._start_tag(best_tag_name)
            
        elif earliest_close != -1:
            # Process closing tag
            if earliest_close > 0:
                # Yield content before the closing tag
                content = self.buffer[:earliest_close]
                if self.tag_stack:
                    current_tag = self.current_tag()
                    current_tag.add_content(content)
                    if current_tag.config.behavior != TagBehavior.SILENT:
                        yield StreamingEvent(
                            event_type=EventType.TAG_CONTENT,
                            tag_name=current_tag.name,
                            content=content,
                            data=current_tag.config
                        )
            
            # Close the tag
            self.buffer = self.buffer[earliest_close + close_tag_len:]
            yield from self._close_tag(close_tag_name)
            
        else:
            # No complete tags found
            if len(self.buffer) >= self._max_tag_length():
                # Buffer is longer than any possible tag, yield excess content
                excess_len = len(self.buffer) - self._max_tag_length() + 1
                content = self.buffer[:excess_len]
                if self.tag_stack:
                    current_tag = self.current_tag()
                    current_tag.add_content(content)
                    # Only emit content event if current tag is not silent
                    if current_tag.config.behavior != TagBehavior.SILENT:
                        yield StreamingEvent(
                            event_type=EventType.TAG_CONTENT,
                            tag_name=current_tag.name,
                            content=content,
                            data=current_tag.config
                        )
                else:
                    # No tags on stack, this is regular content
                    yield StreamingEvent(event_type=EventType.CONTENT, content=content)
                self.buffer = self.buffer[excess_len:]
            else:
                # Buffer might contain partial tag, wait for more content
                return
                
    def _start_tag(self, tag_name: str) -> Generator[StreamingEvent, None, None]:
        """Start processing a new tag."""
        if tag_name not in self.tag_configs:
            raise TagNotFoundError(tag_name, f"No configuration found for tag '{tag_name}'")
            
        config = self.tag_configs[tag_name]
        tag_state = TagState(name=tag_name, config=config, start_position=len(self.buffer))
        
        self.tag_stack.append(tag_state)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Started tag: {tag_name}, stack depth: {len(self.tag_stack)}")
        
        # Execute start callback if configured
        if config.start_callback:
            try:
                config.start_callback(tag_name)
            except Exception as e:
                logger.error(f"Error in start callback for tag {tag_name}: {e}")
        
        # Emit tag start event
        yield StreamingEvent(event_type=EventType.TAG_START, tag_name=tag_name, data=config)
        
    def _close_tag(self, tag_name: str) -> Generator[StreamingEvent, None, None]:
        """Close a tag by name (handles nested closing)."""
        # Find the tag in the stack (should be the most recent matching tag)
        tag_index = -1
        for i in range(len(self.tag_stack) - 1, -1, -1):
            if self.tag_stack[i].name == tag_name:
                tag_index = i
                break
        
        if tag_index == -1:
            if logger.isEnabledFor(logging.WARNING):
                logger.warning(f"Attempted to close tag {tag_name} but it's not in the stack")
            return
        
        # Close all tags from the top down to the target tag
        while len(self.tag_stack) > tag_index:
            tag_state = self.tag_stack.pop()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Closed tag: {tag_state.name}, stack depth: {len(self.tag_stack)}")
            
            # Execute complete callback if configured
            if tag_state.config.complete_callback:
                try:
                    tag_state.config.complete_callback(tag_state.name, tag_state.content)
                except Exception as e:
                    logger.error(f"Error in complete callback for tag {tag_state.name}: {e}")
            
            # Emit tag complete event
            yield StreamingEvent(
                event_type=EventType.TAG_COMPLETE,
                tag_name=tag_state.name,
                content=tag_state.content,
                data=tag_state.config
            )
    
    def _close_current_tag(self) -> None:
        """Close the current (top) tag without emitting events."""
        if self.tag_stack:
            tag_state = self.tag_stack.pop()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Closed current tag: {tag_state.name}, stack depth: {len(self.tag_stack)}")
            
            # Execute complete callback if configured
            if tag_state.config.complete_callback:
                try:
                    tag_state.config.complete_callback(tag_state.name, tag_state.content)
                except Exception as e:
                    logger.error(f"Error in complete callback for tag {tag_state.name}: {e}")
        
    def _max_tag_length(self) -> int:
        """Calculate the maximum possible tag length for buffer management."""
        if not self.tag_configs:
            return 12  # Default reasonable buffer size
        
        max_len = 0
        for tag_name in self.tag_configs.keys():
            # Account for opening tag: <tagname>
            opening_len = len(f'<{tag_name}>')
            # Account for closing tag: </tagname>
            closing_len = len(f'</{tag_name}>')
            max_len = max(max_len, opening_len, closing_len)
            
        return max_len + 1  # Add buffer for safety
    
    def _validate_configs(self) -> None:
        """Validate all tag configurations."""
        for tag_name, config in self.tag_configs.items():
            if config.name != tag_name:
                raise ValueError(f"Tag config name '{config.name}' doesn't match key '{tag_name}'")
            config.validate_callbacks()
    
    def get_stack_depth(self) -> int:
        """Get the current stack depth."""
        return len(self.tag_stack)
    
    def get_buffer_size(self) -> int:
        """Get the current buffer size."""
        return len(self.buffer)
    
    def get_stack_info(self) -> List[Dict[str, str]]:
        """
        Get information about the current tag stack.
        
        Returns:
            List of dictionaries with tag information
        """
        return [
            {
                "name": tag_state.name,
                "behavior": str(tag_state.config.behavior),
                "content_length": str(tag_state.get_content_length())
            }
            for tag_state in self.tag_stack
        ] 