"""
Tag behavior definitions for the streaming XML parser.

This module defines the different behaviors that can be applied to XML tags
during parsing, determining how content is processed and output.
"""

from enum import Enum


class TagBehavior(Enum):
    """
    Defines the behavior type for different XML tags.
    
    Attributes:
        STREAMING: Stream content immediately as it arrives (blocks nesting)
        PLACEHOLDER: Show status message during processing (allows nesting)  
        SILENT: Process silently without user feedback (allows nesting)
    """
    STREAMING = "streaming"      # Stream content immediately as it arrives (blocks nesting)
    PLACEHOLDER = "placeholder"  # Show status message during processing (allows nesting)
    SILENT = "silent"           # Process silently without user feedback (allows nesting)
    
    def __str__(self) -> str:
        """Return the string representation of the behavior."""
        return self.value
    
    def blocks_nesting(self) -> bool:
        """
        Check if this behavior blocks nesting of child tags.
        
        Returns:
            bool: True if nesting is blocked, False otherwise
        """
        return self == TagBehavior.STREAMING
    
    def allows_nesting(self) -> bool:
        """
        Check if this behavior allows nesting of child tags.
        
        Returns:
            bool: True if nesting is allowed, False otherwise
        """
        return not self.blocks_nesting() 