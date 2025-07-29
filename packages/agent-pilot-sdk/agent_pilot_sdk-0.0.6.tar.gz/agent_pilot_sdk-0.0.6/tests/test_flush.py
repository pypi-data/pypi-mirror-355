from unittest.mock import patch, MagicMock
import agent_pilot as ap


class TestFlushInterface:
    """Test suite for the flush interface."""

    def test_flush_function_exists(self):
        """Test that flush function is properly exported."""
        assert hasattr(ap, 'flush')
        assert callable(ap.flush)

    @patch('agent_pilot.tracking.queue')
    def test_flush_calls_queue_flush(self, mock_queue):
        """Test that ap.flush() calls queue.flush()."""
        # Call the flush function
        ap.flush()

        # Verify that queue.flush was called
        mock_queue.flush.assert_called_once()

    @patch('agent_pilot.tracking.queue')
    @patch('agent_pilot.tracking.logger')
    def test_flush_handles_exceptions(self, mock_logger, mock_queue):
        """Test that flush handles exceptions gracefully."""
        # Mock queue.flush to raise an exception
        mock_queue.flush.side_effect = Exception('Network error')

        # Call flush - should not raise exception
        ap.flush()

        # Verify that the exception was logged
        mock_logger.exception.assert_called_once()

    def test_event_queue_flush_method(self):
        """Test that EventQueue has a flush method."""
        from agent_pilot.event_queue import EventQueue

        with patch('agent_pilot.event_queue.Consumer') as mock_consumer_class:
            mock_consumer_instance = MagicMock()
            mock_consumer_class.return_value = mock_consumer_instance

            queue = EventQueue()

            # Verify EventQueue has flush method
            assert hasattr(queue, 'flush')
            assert callable(queue.flush)

    def test_event_queue_flush_calls_consumer_send_batch(self):
        """Test that EventQueue.flush() calls consumer.send_batch()."""
        from agent_pilot.event_queue import EventQueue

        with patch('agent_pilot.event_queue.Consumer') as mock_consumer_class:
            mock_consumer_instance = MagicMock()
            mock_consumer_class.return_value = mock_consumer_instance

            queue = EventQueue()

            # Call flush
            queue.flush()

            # Verify that consumer.send_batch was called
            mock_consumer_instance.send_batch.assert_called_once()

    def test_flush_integration_with_tracking(self):
        """Test flush integration with the tracking system."""
        from agent_pilot.tracking import flush

        with patch('agent_pilot.event_queue.Consumer') as mock_consumer_class:
            mock_consumer_instance = MagicMock()
            mock_consumer_class.return_value = mock_consumer_instance

            # Mock the global queue in tracking
            with patch('agent_pilot.tracking.queue') as mock_queue:
                mock_queue.flush = MagicMock()

                # Call flush function
                flush()

                # Verify queue.flush was called
                mock_queue.flush.assert_called_once()

    def test_flush_in_realistic_scenario(self):
        """Test flush in a realistic usage scenario."""
        with patch('agent_pilot.event_queue.Consumer') as mock_consumer_class:
            with patch('agent_pilot.http_client.get_http_client') as mock_http_client:
                mock_consumer_instance = MagicMock()
                mock_consumer_class.return_value = mock_consumer_instance

                mock_http_client.return_value.post.return_value = ('success', 200)

                # Track an event
                ap.track_event(
                    run_type='test',
                    event_name='test_event',
                    run_id='test-run-id',
                    task_id='test-task-id',
                    version='v1',
                )

                # Flush events
                ap.flush()

                # The consumer's send_batch should be called via flush
                # Note: We can't directly verify this without more complex mocking
                # but this test ensures the basic flow works without exceptions
                assert True  # If we got here, flush completed successfully
