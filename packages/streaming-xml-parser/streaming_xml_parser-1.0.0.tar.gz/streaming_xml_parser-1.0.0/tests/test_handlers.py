"""
Tests for the handlers module (output handlers).
"""

import pytest
import io
from typing import List, Tuple, Any

from xmlstream import (
    StreamingOutputHandler,
    CollectingOutputHandler,
    CallbackOutputHandler,
    StreamingEvent,
    EventType,
    TagConfig,
    TagBehavior
)


class TestStreamingOutputHandler:
    """Test StreamingOutputHandler functionality."""
    
    def test_init_default(self):
        """Test StreamingOutputHandler initialization with defaults."""
        handler = StreamingOutputHandler()
        assert handler.placeholder_prefix == "\n"
        assert handler.placeholder_suffix == " ✓\n"
        assert handler.enable_colors is True
        assert handler.active_placeholders == {}
    
    def test_init_custom_parameters(self, mock_writer):
        """Test StreamingOutputHandler initialization with custom parameters."""
        handler = StreamingOutputHandler(
            output_writer=mock_writer,
            placeholder_prefix="[",
            placeholder_suffix="] DONE\n",
            enable_colors=False
        )
        assert handler.output_writer == mock_writer
        assert handler.placeholder_prefix == "["
        assert handler.placeholder_suffix == "] DONE\n"
        assert handler.enable_colors is False
    
    def test_handle_content_event(self, mock_writer):
        """Test handling content events."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        event = StreamingEvent(EventType.CONTENT, content="Hello World")
        
        handler.handle_event(event)
        
        assert mock_writer.get_output() == "Hello World"
        assert mock_writer.flushed is True
    
    def test_handle_content_event_empty(self, mock_writer):
        """Test handling content events with empty content."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        event = StreamingEvent(EventType.CONTENT, content="")
        
        handler.handle_event(event)
        
        assert mock_writer.get_output() == ""
        assert mock_writer.flushed is False
    
    def test_handle_tag_start_streaming(self, mock_writer):
        """Test handling tag start events for streaming behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('stream', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_START, tag_name='stream', data=config)
        
        handler.handle_event(event)
        
        # Streaming behavior should not output anything on start
        assert mock_writer.get_output() == ""
        assert 'stream' not in handler.active_placeholders
    
    def test_handle_tag_start_placeholder(self, mock_writer):
        """Test handling tag start events for placeholder behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('placeholder', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        event = StreamingEvent(EventType.TAG_START, tag_name='placeholder', data=config)
        
        handler.handle_event(event)
        
        assert mock_writer.get_output() == "\nLoading..."
        assert handler.active_placeholders['placeholder'] is True
    
    def test_handle_tag_start_silent(self, mock_writer):
        """Test handling tag start events for silent behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('silent', TagBehavior.SILENT)
        event = StreamingEvent(EventType.TAG_START, tag_name='silent', data=config)
        
        handler.handle_event(event)
        
        # Silent behavior should not output anything
        assert mock_writer.get_output() == ""
        assert 'silent' not in handler.active_placeholders
    
    def test_handle_tag_content_streaming(self, mock_writer):
        """Test handling tag content events for streaming behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('stream', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_CONTENT, tag_name='stream', content='streaming data', data=config)
        
        handler.handle_event(event)
        
        assert mock_writer.get_output() == "streaming data"
    
    def test_handle_tag_content_non_streaming(self, mock_writer):
        """Test handling tag content events for non-streaming behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('placeholder', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        event = StreamingEvent(EventType.TAG_CONTENT, tag_name='placeholder', content='content', data=config)
        
        handler.handle_event(event)
        
        # Non-streaming behaviors should not output content during processing
        assert mock_writer.get_output() == ""
    
    def test_handle_tag_complete_placeholder(self, mock_writer):
        """Test handling tag complete events for placeholder behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('placeholder', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        
        # First start the placeholder
        start_event = StreamingEvent(EventType.TAG_START, tag_name='placeholder', data=config)
        handler.handle_event(start_event)
        
        # Then complete it
        complete_event = StreamingEvent(EventType.TAG_COMPLETE, tag_name='placeholder', data=config)
        handler.handle_event(complete_event)
        
        assert mock_writer.get_output() == "\nLoading... ✓\n"
        assert 'placeholder' not in handler.active_placeholders
    
    def test_handle_tag_complete_streaming(self, mock_writer):
        """Test handling tag complete events for streaming behavior."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        config = TagConfig('stream', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_COMPLETE, tag_name='stream', data=config)
        
        handler.handle_event(event)
        
        # Streaming behavior should not output anything special on complete
        assert mock_writer.get_output() == ""
    
    def test_reset(self, mock_writer):
        """Test handler reset functionality."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        
        # Add some active placeholders
        handler.active_placeholders['test1'] = True
        handler.active_placeholders['test2'] = True
        
        handler.reset()
        
        assert handler.active_placeholders == {}
    
    def test_handle_event_without_data(self, mock_writer):
        """Test handling events without data attribute."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        event = StreamingEvent(EventType.TAG_START, tag_name='test')  # No data
        
        # Should not raise exception
        handler.handle_event(event)
        assert mock_writer.get_output() == ""


class TestCollectingOutputHandler:
    """Test CollectingOutputHandler functionality."""
    
    def test_init(self):
        """Test CollectingOutputHandler initialization."""
        handler = CollectingOutputHandler()
        assert handler.buffer == []
        assert handler.events == []
    
    def test_handle_content_event(self):
        """Test handling content events."""
        handler = CollectingOutputHandler()
        event = StreamingEvent(EventType.CONTENT, content="Hello World")
        
        handler.handle_event(event)
        
        assert len(handler.events) == 1
        assert handler.events[0] == event
        assert handler.buffer == ["Hello World"]
    
    def test_handle_tag_content_event(self):
        """Test handling tag content events."""
        handler = CollectingOutputHandler()
        config = TagConfig('stream', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_CONTENT, tag_name='stream', content='data', data=config)
        
        handler.handle_event(event)
        
        assert len(handler.events) == 1
        assert handler.events[0] == event
        assert handler.buffer == ["data"]
    
    def test_handle_tag_start_event(self):
        """Test handling tag start events."""
        handler = CollectingOutputHandler()
        config = TagConfig('test', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_START, tag_name='test', data=config)
        
        handler.handle_event(event)
        
        assert len(handler.events) == 1
        assert handler.events[0] == event
        assert handler.buffer == []  # No content for tag start
    
    def test_handle_event_without_content(self):
        """Test handling events without content."""
        handler = CollectingOutputHandler()
        event = StreamingEvent(EventType.TAG_START, tag_name='test')
        
        handler.handle_event(event)
        
        assert len(handler.events) == 1
        assert handler.buffer == []
    
    def test_get_content_empty(self):
        """Test getting content when empty."""
        handler = CollectingOutputHandler()
        assert handler.get_content() == ""
    
    def test_get_content_with_data(self):
        """Test getting content with collected data."""
        handler = CollectingOutputHandler()
        
        events = [
            StreamingEvent(EventType.CONTENT, content="Hello "),
            StreamingEvent(EventType.TAG_CONTENT, tag_name='test', content="World"),
            StreamingEvent(EventType.CONTENT, content="!")
        ]
        
        for event in events:
            handler.handle_event(event)
        
        assert handler.get_content() == "Hello World!"
    
    def test_get_events_empty(self):
        """Test getting events when empty."""
        handler = CollectingOutputHandler()
        events = handler.get_events()
        assert events == []
        assert isinstance(events, list)
    
    def test_get_events_returns_copy(self):
        """Test that get_events returns a copy."""
        handler = CollectingOutputHandler()
        event = StreamingEvent(EventType.CONTENT, content="test")
        handler.handle_event(event)
        
        events1 = handler.get_events()
        events2 = handler.get_events()
        
        assert events1 == events2
        assert events1 is not events2  # Should be different objects
        
        # Modifying returned list shouldn't affect handler
        events1.append(StreamingEvent(EventType.CONTENT, content="extra"))
        assert len(handler.get_events()) == 1
    
    def test_clear(self):
        """Test clearing collected data."""
        handler = CollectingOutputHandler()
        
        # Add some data
        events = [
            StreamingEvent(EventType.CONTENT, content="Hello"),
            StreamingEvent(EventType.TAG_START, tag_name='test')
        ]
        
        for event in events:
            handler.handle_event(event)
        
        # Verify data exists
        assert len(handler.buffer) > 0
        assert len(handler.events) > 0
        
        # Clear and verify
        handler.clear()
        assert handler.buffer == []
        assert handler.events == []
        assert handler.get_content() == ""
        assert handler.get_events() == []


class TestCallbackOutputHandler:
    """Test CallbackOutputHandler functionality."""
    
    def test_init_no_callbacks(self):
        """Test CallbackOutputHandler initialization without callbacks."""
        handler = CallbackOutputHandler()
        assert handler.on_content is None
        assert handler.on_tag_start is None
        assert handler.on_tag_content is None
        assert handler.on_tag_complete is None
    
    def test_init_with_callbacks(self):
        """Test CallbackOutputHandler initialization with callbacks."""
        def content_cb(content): pass
        def start_cb(tag, data): pass
        def tag_content_cb(tag, content, data): pass
        def complete_cb(tag, content, data): pass
        
        handler = CallbackOutputHandler(
            on_content=content_cb,
            on_tag_start=start_cb,
            on_tag_content=tag_content_cb,
            on_tag_complete=complete_cb
        )
        
        assert handler.on_content == content_cb
        assert handler.on_tag_start == start_cb
        assert handler.on_tag_content == tag_content_cb
        assert handler.on_tag_complete == complete_cb
    
    def test_handle_content_event_with_callback(self):
        """Test handling content events with callback."""
        called_with = []
        
        def content_callback(content):
            called_with.append(content)
        
        handler = CallbackOutputHandler(on_content=content_callback)
        event = StreamingEvent(EventType.CONTENT, content="Hello World")
        
        handler.handle_event(event)
        
        assert called_with == ["Hello World"]
    
    def test_handle_content_event_without_callback(self):
        """Test handling content events without callback."""
        handler = CallbackOutputHandler()
        event = StreamingEvent(EventType.CONTENT, content="Hello World")
        
        # Should not raise exception
        handler.handle_event(event)
    
    def test_handle_tag_start_event_with_callback(self):
        """Test handling tag start events with callback."""
        called_with = []
        
        def start_callback(tag_name, data):
            called_with.append((tag_name, data))
        
        handler = CallbackOutputHandler(on_tag_start=start_callback)
        config = TagConfig('test', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_START, tag_name='test', data=config)
        
        handler.handle_event(event)
        
        assert len(called_with) == 1
        assert called_with[0][0] == 'test'
        assert called_with[0][1] == config
    
    def test_handle_tag_content_event_with_callback(self):
        """Test handling tag content events with callback."""
        called_with = []
        
        def content_callback(tag_name, content, data):
            called_with.append((tag_name, content, data))
        
        handler = CallbackOutputHandler(on_tag_content=content_callback)
        config = TagConfig('stream', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_CONTENT, tag_name='stream', content='data', data=config)
        
        handler.handle_event(event)
        
        assert len(called_with) == 1
        assert called_with[0] == ('stream', 'data', config)
    
    def test_handle_tag_complete_event_with_callback(self):
        """Test handling tag complete events with callback."""
        called_with = []
        
        def complete_callback(tag_name, content, data):
            called_with.append((tag_name, content, data))
        
        handler = CallbackOutputHandler(on_tag_complete=complete_callback)
        config = TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        event = StreamingEvent(EventType.TAG_COMPLETE, tag_name='test', content='final', data=config)
        
        handler.handle_event(event)
        
        assert len(called_with) == 1
        assert called_with[0] == ('test', 'final', config)
    
    def test_handle_events_with_empty_content(self):
        """Test handling events with empty or None content."""
        content_calls = []
        tag_content_calls = []
        
        def content_callback(content):
            content_calls.append(content)
        
        def tag_content_callback(tag, content, data):
            tag_content_calls.append((tag, content, data))
        
        handler = CallbackOutputHandler(
            on_content=content_callback,
            on_tag_content=tag_content_callback
        )
        
        # Test with None content
        event1 = StreamingEvent(EventType.CONTENT, content=None)
        handler.handle_event(event1)
        
        # Test with empty content
        event2 = StreamingEvent(EventType.TAG_CONTENT, tag_name='test', content="")
        handler.handle_event(event2)
        
        assert content_calls == [""]  # None gets converted to ""
        assert tag_content_calls == [('test', "", None)]


class TestHandlerIntegration:
    """Test handler integration scenarios."""
    
    def test_multiple_handlers_same_events(self):
        """Test multiple handlers processing the same events."""
        # Set up handlers
        collecting_handler = CollectingOutputHandler()
        
        callback_data = []
        def callback(content):
            callback_data.append(content)
        callback_handler = CallbackOutputHandler(on_content=callback)
        
        # Create events
        events = [
            StreamingEvent(EventType.CONTENT, content="Hello "),
            StreamingEvent(EventType.CONTENT, content="World!")
        ]
        
        # Process with both handlers
        for event in events:
            collecting_handler.handle_event(event)
            callback_handler.handle_event(event)
        
        # Verify both handlers processed events correctly
        assert collecting_handler.get_content() == "Hello World!"
        assert callback_data == ["Hello ", "World!"]
    
    def test_handler_with_complete_parsing_flow(self, mock_writer):
        """Test handler with complete parsing flow simulation."""
        handler = StreamingOutputHandler(output_writer=mock_writer)
        
        # Simulate a complete parsing flow
        config = TagConfig('stream', TagBehavior.STREAMING)
        
        events = [
            StreamingEvent(EventType.CONTENT, content="Before "),
            StreamingEvent(EventType.TAG_START, tag_name='stream', data=config),
            StreamingEvent(EventType.TAG_CONTENT, tag_name='stream', content='streaming content', data=config),
            StreamingEvent(EventType.TAG_COMPLETE, tag_name='stream', content='streaming content', data=config),
            StreamingEvent(EventType.CONTENT, content=" After")
        ]
        
        for event in events:
            handler.handle_event(event)
        
        assert mock_writer.get_output() == "Before streaming content After"
    
    def test_placeholder_workflow(self, mock_writer):
        """Test complete placeholder behavior workflow."""
        handler = StreamingOutputHandler(
            output_writer=mock_writer,
            placeholder_prefix="[",
            placeholder_suffix="] ✓\n"
        )
        
        config = TagConfig('task', TagBehavior.PLACEHOLDER, placeholder_message='Processing task...')
        
        events = [
            StreamingEvent(EventType.TAG_START, tag_name='task', data=config),
            StreamingEvent(EventType.TAG_COMPLETE, tag_name='task', content='task result', data=config)
        ]
        
        for event in events:
            handler.handle_event(event)
        
        assert mock_writer.get_output() == "[Processing task...] ✓\n"
        assert handler.active_placeholders == {} 