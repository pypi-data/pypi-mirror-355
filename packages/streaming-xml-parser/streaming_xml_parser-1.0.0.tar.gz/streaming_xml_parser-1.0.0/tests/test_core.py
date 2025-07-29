"""
Tests for the core StreamingXMLParser class.
"""

import pytest
from typing import List

from xmlstream import (
    StreamingXMLParser,
    TagConfig,
    TagBehavior,
    StreamingEvent,
    EventType,
    BufferOverflowError,
    TagNotFoundError,
    InvalidTagError
)


class TestStreamingXMLParserInit:
    """Test parser initialization and configuration."""
    
    def test_init_with_configs(self, basic_tag_configs):
        """Test parser initialization with tag configurations."""
        parser = StreamingXMLParser(basic_tag_configs)
        assert parser.tag_configs == basic_tag_configs
        assert parser.max_buffer_size == StreamingXMLParser.DEFAULT_MAX_BUFFER_SIZE
        assert parser.buffer == ""
        assert parser.tag_stack == []
    
    def test_init_with_custom_buffer_size(self, basic_tag_configs):
        """Test parser initialization with custom buffer size."""
        custom_size = 2048
        parser = StreamingXMLParser(basic_tag_configs, max_buffer_size=custom_size)
        assert parser.max_buffer_size == custom_size
    
    def test_init_empty_configs(self):
        """Test parser initialization with empty configurations."""
        parser = StreamingXMLParser({})
        assert parser.tag_configs == {}


class TestParserState:
    """Test parser state management."""
    
    def test_reset(self, parser):
        """Test parser reset functionality."""
        # Add some state
        parser.buffer = "test content"
        parser.tag_stack.append("dummy")
        
        # Reset and verify
        parser.reset()
        assert parser.buffer == ""
        assert parser.tag_stack == []
    
    def test_is_streaming_mode_empty_stack(self, parser):
        """Test streaming mode check with empty stack."""
        assert not parser.is_streaming_mode()
    
    def test_is_streaming_mode_with_streaming_tag(self, parser):
        """Test streaming mode check with streaming tag on stack."""
        from xmlstream.config import TagState
        
        streaming_config = TagConfig('test', TagBehavior.STREAMING)
        tag_state = TagState('test', streaming_config)
        parser.tag_stack.append(tag_state)
        
        assert parser.is_streaming_mode()
    
    def test_is_streaming_mode_with_non_streaming_tag(self, parser):
        """Test streaming mode check with non-streaming tag on stack."""
        from xmlstream.config import TagState
        
        silent_config = TagConfig('test', TagBehavior.SILENT)
        tag_state = TagState('test', silent_config)
        parser.tag_stack.append(tag_state)
        
        assert not parser.is_streaming_mode()
    
    def test_current_tag_empty_stack(self, parser):
        """Test current tag with empty stack."""
        assert parser.current_tag() is None
    
    def test_current_tag_with_stack(self, parser):
        """Test current tag with items on stack."""
        from xmlstream.config import TagState
        
        config = TagConfig('test', TagBehavior.SILENT)
        tag_state = TagState('test', config)
        parser.tag_stack.append(tag_state)
        
        assert parser.current_tag() == tag_state


class TestTagConfigManagement:
    """Test tag configuration management."""
    
    def test_add_tag_config(self, parser):
        """Test adding new tag configuration."""
        new_config = TagConfig('newTag', TagBehavior.STREAMING)
        parser.add_tag_config(new_config)
        
        assert 'newTag' in parser.tag_configs
        assert parser.tag_configs['newTag'] == new_config
    
    def test_add_tag_config_override(self, parser):
        """Test overriding existing tag configuration."""
        original_config = parser.tag_configs['stream']
        new_config = TagConfig('stream', TagBehavior.SILENT)
        
        parser.add_tag_config(new_config)
        assert parser.tag_configs['stream'] != original_config
        assert parser.tag_configs['stream'] == new_config
    
    def test_remove_tag_config_existing(self, parser):
        """Test removing existing tag configuration."""
        assert 'stream' in parser.tag_configs
        result = parser.remove_tag_config('stream')
        
        assert result is True
        assert 'stream' not in parser.tag_configs
    
    def test_remove_tag_config_nonexistent(self, parser):
        """Test removing non-existent tag configuration."""
        result = parser.remove_tag_config('nonexistent')
        assert result is False


class TestBasicParsing:
    """Test basic parsing functionality."""
    
    def test_process_empty_chunk(self, parser):
        """Test processing empty chunk."""
        events = list(parser.process_chunk(""))
        assert events == []
    
    def test_process_none_chunk(self, parser):
        """Test processing None chunk."""
        events = list(parser.process_chunk(None))
        assert events == []
    
    def test_simple_content_no_tags(self, parser):
        """Test processing content without any tags."""
        # Short content should be buffered, not immediately output
        events = list(parser.process_chunk("Hello World"))
        assert len(events) == 0  # Content is buffered waiting for potential tags
        
        # Longer content should trigger output when it exceeds max tag length
        long_content = "This is a much longer string that exceeds the maximum possible tag length buffer"
        events = list(parser.process_chunk(long_content))
        assert len(events) >= 1
        assert any(e.event_type == EventType.CONTENT for e in events)
    
    def test_streaming_tag_simple(self, parser, sample_xml):
        """Test simple streaming tag processing."""
        events = list(parser.process_chunk(sample_xml['simple']))
        
        # Should have: tag_start, tag_content, tag_complete
        assert len(events) == 3
        assert events[0].event_type == EventType.TAG_START
        assert events[0].tag_name == 'stream'
        assert events[1].event_type == EventType.TAG_CONTENT
        assert events[1].content == 'Hello World'
        assert events[2].event_type == EventType.TAG_COMPLETE
        assert events[2].tag_name == 'stream'
    
    def test_placeholder_tag_simple(self, parser):
        """Test simple placeholder tag processing."""
        xml = '<placeholder>Content</placeholder>'
        events = list(parser.process_chunk(xml))
        
        # Should have: tag_start, tag_content, tag_complete
        assert len(events) == 3
        assert events[0].event_type == EventType.TAG_START
        assert events[0].tag_name == 'placeholder'
        assert events[1].event_type == EventType.TAG_CONTENT
        assert events[1].tag_name == 'placeholder'
        assert events[1].content == 'Content'
        assert events[2].event_type == EventType.TAG_COMPLETE
        assert events[2].tag_name == 'placeholder'
        assert events[2].content == 'Content'
    
    def test_silent_tag_simple(self, parser):
        """Test simple silent tag processing."""
        xml = '<silent>Content</silent>'
        events = list(parser.process_chunk(xml))
        
        # Should have: tag_start, tag_complete (no content event for silent)
        assert len(events) == 2
        assert events[0].event_type == EventType.TAG_START
        assert events[0].tag_name == 'silent'
        assert events[1].event_type == EventType.TAG_COMPLETE
        assert events[1].tag_name == 'silent'
        assert events[1].content == 'Content'


class TestStreamingBehavior:
    """Test streaming behavior and nesting rules."""
    
    def test_streaming_blocks_nesting(self, parser):
        """Test that streaming tags block nesting."""
        xml = '<stream>Before <nested>Inside</nested> After</stream>'
        events = list(parser.process_chunk(xml))
        
        # Content should be treated as literal text, no nested tag events
        content_events = [e for e in events if e.event_type == EventType.TAG_CONTENT]
        combined_content = ''.join(e.content for e in content_events)
        assert 'Before <nested>Inside</nested> After' == combined_content
    
    def test_chunked_streaming_content(self, parser):
        """Test streaming content delivered in chunks."""
        chunks = ['<stream>Part', ' 1 and', ' Part 2</stream>']
        all_events = []
        
        for chunk in chunks:
            events = list(parser.process_chunk(chunk))
            all_events.extend(events)
        
        # Should have tag_start, multiple tag_content events, and tag_complete
        content_events = [e for e in all_events if e.event_type == EventType.TAG_CONTENT]
        combined_content = ''.join(e.content for e in content_events)
        assert combined_content == 'Part 1 and Part 2'


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_buffer_overflow(self, basic_tag_configs):
        """Test buffer overflow protection."""
        parser = StreamingXMLParser(basic_tag_configs, max_buffer_size=10)
        
        # Use a string longer than the buffer limit
        long_string = "This is a very long string that definitely exceeds the buffer limit of 10 characters"
        with pytest.raises(BufferOverflowError) as exc_info:
            list(parser.process_chunk(long_string))
        
        assert exc_info.value.limit == 10
        assert exc_info.value.buffer_size > 10
    
    def test_unclosed_tag_in_buffer(self, parser):
        """Test handling of unclosed tags."""
        # Send opening tag but no closing tag
        events = list(parser.process_chunk('<stream>Content without closing'))
        
        # Should have tag_start and tag_content, but no tag_complete yet
        assert any(e.event_type == EventType.TAG_START for e in events)
        assert any(e.event_type == EventType.TAG_CONTENT for e in events)
        assert not any(e.event_type == EventType.TAG_COMPLETE for e in events)
    
    def test_malformed_tag_handling(self, parser):
        """Test handling of malformed tags."""
        # Test various malformed scenarios
        malformed_inputs = [
            '<>',  # Empty tag
            '<stream',  # Incomplete opening tag
            'stream>',  # Missing opening bracket
            '< stream>',  # Space after bracket
        ]
        
        for malformed in malformed_inputs:
            # Reset parser for each test
            parser.reset()
            # Malformed tags that don't match configured tags get buffered
            events = list(parser.process_chunk(malformed))
            # Short malformed content gets buffered, not immediately output
            # Only longer content that exceeds buffer thresholds would be output
            # This is correct behavior for a streaming parser
            if len(malformed) < parser._max_tag_length():
                assert len(events) == 0  # Content is buffered
            else:
                assert any(e.event_type == EventType.CONTENT for e in events)


class TestComplexScenarios:
    """Test complex parsing scenarios."""
    
    def test_mixed_content_and_tags(self, parser, sample_xml):
        """Test mixed content with multiple tag types."""
        events = list(parser.process_chunk(sample_xml['mixed']))
        
        # Should handle content before tags, but content after tags may be buffered
        content_events = [e for e in events if e.event_type == EventType.CONTENT]
        # Content before tags should be output, but short content after tags may be buffered
        assert len(content_events) >= 1  # At least "Before " should be output
    
    def test_nested_non_streaming_tags(self, parser):
        """Test nesting with non-streaming tags."""
        xml = '<silent>Before <placeholder>Nested</placeholder> After</silent>'
        events = list(parser.process_chunk(xml))
        
        # Should have events for both outer and inner tags
        tag_starts = [e for e in events if e.event_type == EventType.TAG_START]
        assert len(tag_starts) == 2
        assert any(e.tag_name == 'silent' for e in tag_starts)
        assert any(e.tag_name == 'placeholder' for e in tag_starts)
    
    def test_multiple_chunks_complete_parsing(self, parser):
        """Test complete parsing across multiple chunks."""
        xml_parts = ['<stream>Start', ' middle', ' end</stream> after']
        all_events = []
        
        for part in xml_parts:
            events = list(parser.process_chunk(part))
            all_events.extend(events)
        
        # Verify complete parsing
        assert any(e.event_type == EventType.TAG_START and e.tag_name == 'stream' for e in all_events)
        assert any(e.event_type == EventType.TAG_COMPLETE and e.tag_name == 'stream' for e in all_events)
        # Content after closing tag (" after") gets buffered and may not be immediately output
        # This is correct streaming behavior - short trailing content is held in buffer


class TestParserUtilities:
    """Test utility methods of the parser."""
    
    def test_get_stack_depth(self, parser):
        """Test stack depth reporting."""
        assert parser.get_stack_depth() == 0
        
        # Simulate adding to stack
        from xmlstream.config import TagState
        config = TagConfig('test', TagBehavior.SILENT)
        parser.tag_stack.append(TagState('test', config))
        
        assert parser.get_stack_depth() == 1
    
    def test_get_buffer_size(self, parser):
        """Test buffer size reporting."""
        assert parser.get_buffer_size() == 0
        
        parser.buffer = "test content"
        assert parser.get_buffer_size() == len("test content")
    
    def test_get_stack_info(self, parser):
        """Test stack information reporting."""
        info = parser.get_stack_info()
        assert isinstance(info, list)
        assert len(info) == 0
        
        # Add item to stack and test again
        from xmlstream.config import TagState
        config = TagConfig('test', TagBehavior.STREAMING)
        parser.tag_stack.append(TagState('test', config))
        
        info = parser.get_stack_info()
        assert len(info) == 1
        assert isinstance(info[0], dict) 