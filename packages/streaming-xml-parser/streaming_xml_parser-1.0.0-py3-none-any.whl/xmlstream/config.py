"""
Configuration classes for the streaming XML parser.

This module defines the configuration and state management classes
used to control tag behavior and track parsing state.
"""

from dataclasses import dataclass, field
from typing import Callable, Any, Optional

from .behaviors import TagBehavior
from .exceptions import ConfigurationError


@dataclass
class TagConfig:
    """
    Configuration for how to handle a specific XML tag.
    
    This class defines the behavior and callbacks for a specific XML tag
    during parsing. It includes validation to ensure configurations are valid.
    
    Attributes:
        name: The name of the XML tag
        behavior: The behavior type for this tag
        placeholder_message: Optional message to show during placeholder behavior
        start_callback: Optional callback when tag starts
        content_callback: Optional callback for tag content
        complete_callback: Optional callback when tag completes
    """
    name: str
    behavior: TagBehavior
    placeholder_message: Optional[str] = None
    start_callback: Optional[Callable[[str], Any]] = None
    content_callback: Optional[Callable[[str], Any]] = None
    complete_callback: Optional[Callable[[str, str], Any]] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name or not self.name.strip():
            raise ConfigurationError("Tag name cannot be empty")
            
        if not isinstance(self.behavior, TagBehavior):
            raise ConfigurationError(f"behavior must be a TagBehavior enum, got {type(self.behavior)}")
            
        # Validate placeholder message is provided for PLACEHOLDER behavior
        if self.behavior == TagBehavior.PLACEHOLDER and not self.placeholder_message:
            raise ConfigurationError("placeholder_message is required for PLACEHOLDER behavior")
        
        # Validate callbacks during initialization
        self.validate_callbacks()
    
    def has_callbacks(self) -> bool:
        """Check if this configuration has any callbacks defined."""
        return any([
            self.start_callback is not None,
            self.content_callback is not None,
            self.complete_callback is not None
        ])
    
    def validate_callbacks(self) -> bool:
        """
        Validate that all callbacks are callable.
        
        Returns:
            bool: True if all non-None callbacks are callable
            
        Raises:
            ConfigurationError: If any callback is not callable
        """
        callbacks = [
            ("start_callback", self.start_callback),
            ("content_callback", self.content_callback),
            ("complete_callback", self.complete_callback)
        ]
        
        for name, callback in callbacks:
            if callback is not None and not callable(callback):
                raise ConfigurationError(f"{name} must be callable, got {type(callback)}")
        
        return True


@dataclass
class TagState:
    """
    Represents the state of a tag in the parsing stack.
    
    This class tracks the current state of an active tag during parsing,
    including its content accumulation and position information.
    
    Attributes:
        name: The name of the tag
        config: The configuration for this tag
        content: Accumulated content for this tag
        start_position: Buffer position where the tag started
    """
    name: str
    config: TagConfig
    content: str = ""
    start_position: int = 0
    
    def add_content(self, new_content: str) -> None:
        """
        Add content to this tag state.
        
        Args:
            new_content: The content to add
        """
        if new_content:
            self.content += new_content
    
    def get_content_length(self) -> int:
        """Get the current length of accumulated content."""
        return len(self.content)
    
    def clear_content(self) -> str:
        """
        Clear and return the current content.
        
        Returns:
            str: The content that was cleared
        """
        content = self.content
        self.content = ""
        return content
    
    def is_streaming(self) -> bool:
        """Check if this tag uses streaming behavior."""
        return self.config.behavior == TagBehavior.STREAMING
    
    def is_placeholder(self) -> bool:
        """Check if this tag uses placeholder behavior."""
        return self.config.behavior == TagBehavior.PLACEHOLDER
        
    def is_silent(self) -> bool:
        """Check if this tag uses silent behavior."""
        return self.config.behavior == TagBehavior.SILENT 