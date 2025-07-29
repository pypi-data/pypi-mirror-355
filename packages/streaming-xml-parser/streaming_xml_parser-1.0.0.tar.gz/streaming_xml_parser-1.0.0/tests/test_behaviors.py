"""
Tests for the behaviors module (TagBehavior enum).
"""

import pytest
from xmlstream import TagBehavior


class TestTagBehavior:
    """Test TagBehavior enum functionality."""
    
    def test_enum_values(self):
        """Test TagBehavior enum values are correct."""
        assert TagBehavior.STREAMING.value == "streaming"
        assert TagBehavior.PLACEHOLDER.value == "placeholder"
        assert TagBehavior.SILENT.value == "silent"
    
    def test_string_representation(self):
        """Test TagBehavior string representation."""
        assert str(TagBehavior.STREAMING) == "streaming"
        assert str(TagBehavior.PLACEHOLDER) == "placeholder"
        assert str(TagBehavior.SILENT) == "silent"
    
    def test_enum_membership(self):
        """Test TagBehavior enum membership."""
        assert TagBehavior.STREAMING in TagBehavior
        assert TagBehavior.PLACEHOLDER in TagBehavior
        assert TagBehavior.SILENT in TagBehavior
    
    def test_enum_iteration(self):
        """Test TagBehavior enum iteration."""
        behaviors = list(TagBehavior)
        assert len(behaviors) == 3
        assert TagBehavior.STREAMING in behaviors
        assert TagBehavior.PLACEHOLDER in behaviors
        assert TagBehavior.SILENT in behaviors
    
    def test_equality(self):
        """Test TagBehavior equality comparison."""
        assert TagBehavior.STREAMING == TagBehavior.STREAMING
        assert TagBehavior.PLACEHOLDER == TagBehavior.PLACEHOLDER
        assert TagBehavior.SILENT == TagBehavior.SILENT
        
        assert TagBehavior.STREAMING != TagBehavior.PLACEHOLDER
        assert TagBehavior.STREAMING != TagBehavior.SILENT
        assert TagBehavior.PLACEHOLDER != TagBehavior.SILENT


class TestTagBehaviorNestingMethods:
    """Test TagBehavior nesting-related methods."""
    
    def test_blocks_nesting_streaming(self):
        """Test blocks_nesting returns True for STREAMING behavior."""
        assert TagBehavior.STREAMING.blocks_nesting() is True
    
    def test_blocks_nesting_placeholder(self):
        """Test blocks_nesting returns False for PLACEHOLDER behavior."""
        assert TagBehavior.PLACEHOLDER.blocks_nesting() is False
    
    def test_blocks_nesting_silent(self):
        """Test blocks_nesting returns False for SILENT behavior."""
        assert TagBehavior.SILENT.blocks_nesting() is False
    
    def test_allows_nesting_streaming(self):
        """Test allows_nesting returns False for STREAMING behavior."""
        assert TagBehavior.STREAMING.allows_nesting() is False
    
    def test_allows_nesting_placeholder(self):
        """Test allows_nesting returns True for PLACEHOLDER behavior."""
        assert TagBehavior.PLACEHOLDER.allows_nesting() is True
    
    def test_allows_nesting_silent(self):
        """Test allows_nesting returns True for SILENT behavior."""
        assert TagBehavior.SILENT.allows_nesting() is True
    
    def test_nesting_methods_consistency(self):
        """Test that blocks_nesting and allows_nesting are consistent."""
        for behavior in TagBehavior:
            # These should be opposites of each other
            assert behavior.blocks_nesting() != behavior.allows_nesting()


class TestTagBehaviorIntegration:
    """Test TagBehavior integration scenarios."""
    
    def test_behavior_from_string(self):
        """Test creating TagBehavior from string values."""
        # Test that we can create behaviors from their string values
        streaming = TagBehavior("streaming")
        placeholder = TagBehavior("placeholder")
        silent = TagBehavior("silent")
        
        assert streaming == TagBehavior.STREAMING
        assert placeholder == TagBehavior.PLACEHOLDER
        assert silent == TagBehavior.SILENT
    
    def test_behavior_invalid_string(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            TagBehavior("invalid_behavior")
    
    def test_behavior_case_sensitivity(self):
        """Test that behavior string matching is case sensitive."""
        with pytest.raises(ValueError):
            TagBehavior("STREAMING")
        
        with pytest.raises(ValueError):
            TagBehavior("Streaming")
    
    def test_behavior_with_tag_config(self):
        """Test TagBehavior integration with TagConfig."""
        from xmlstream import TagConfig
        
        # Test all behaviors work with TagConfig
        streaming_config = TagConfig('test', TagBehavior.STREAMING)
        assert streaming_config.behavior == TagBehavior.STREAMING
        assert streaming_config.behavior.blocks_nesting() is True
        
        placeholder_config = TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        assert placeholder_config.behavior == TagBehavior.PLACEHOLDER
        assert placeholder_config.behavior.allows_nesting() is True
        
        silent_config = TagConfig('test', TagBehavior.SILENT)
        assert silent_config.behavior == TagBehavior.SILENT
        assert silent_config.behavior.allows_nesting() is True
    
    def test_behavior_documentation_consistency(self):
        """Test that behavior documentation is consistent with implementation."""
        # STREAMING should block nesting according to docstring
        assert TagBehavior.STREAMING.blocks_nesting() is True
        
        # PLACEHOLDER and SILENT should allow nesting according to docstring
        assert TagBehavior.PLACEHOLDER.allows_nesting() is True
        assert TagBehavior.SILENT.allows_nesting() is True
    
    def test_all_behaviors_have_string_values(self):
        """Test that all behaviors have proper string values."""
        for behavior in TagBehavior:
            # Each behavior should have a non-empty string value
            assert isinstance(behavior.value, str)
            assert len(behavior.value) > 0
            assert behavior.value.islower()  # Should be lowercase
            assert ' ' not in behavior.value  # Should not contain spaces
    
    def test_behavior_hashability(self):
        """Test that TagBehavior values are hashable."""
        # Should be able to use as dictionary keys
        behavior_dict = {
            TagBehavior.STREAMING: "streaming_handler",
            TagBehavior.PLACEHOLDER: "placeholder_handler",
            TagBehavior.SILENT: "silent_handler"
        }
        
        assert behavior_dict[TagBehavior.STREAMING] == "streaming_handler"
        assert behavior_dict[TagBehavior.PLACEHOLDER] == "placeholder_handler"
        assert behavior_dict[TagBehavior.SILENT] == "silent_handler"
        
        # Should be able to use in sets
        behavior_set = {TagBehavior.STREAMING, TagBehavior.PLACEHOLDER, TagBehavior.SILENT}
        assert len(behavior_set) == 3
        assert TagBehavior.STREAMING in behavior_set
        assert TagBehavior.PLACEHOLDER in behavior_set
        assert TagBehavior.SILENT in behavior_set 