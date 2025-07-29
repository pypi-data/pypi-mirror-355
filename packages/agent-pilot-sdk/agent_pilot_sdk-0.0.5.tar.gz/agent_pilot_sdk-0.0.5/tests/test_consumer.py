import pytest
from unittest.mock import Mock, patch
from threading import Thread
from src.agent_pilot.consumer import Consumer
from src.agent_pilot.models import TrackingEvent


class TestConsumer:
    """Test suite for the Consumer class."""

    @pytest.fixture
    def mock_event_queue(self):
        """Create a mock event queue for testing."""
        queue = Mock()
        queue.get_batch.return_value = []
        queue.append = Mock()
        return queue

    @pytest.fixture
    def mock_config(self):
        """Create a mock config object."""
        config = Mock()
        config.verbose = False
        config.api_url = 'https://test-api.com'
        config.api_key = 'test-api-key'
        config.local_debug = False
        return config

    @pytest.fixture
    def mock_tracking_event(self):
        """Create a mock tracking event."""
        event = Mock(spec=TrackingEvent)
        event.run_id = 'test-run-id'
        event.task_id = 'test-task-id'
        event.model_dump.return_value = {'run_id': 'test-run-id', 'task_id': 'test-task-id', 'event_type': 'test'}
        return event

    @pytest.fixture
    def consumer(self, mock_event_queue):
        """Create a Consumer instance for testing."""
        return Consumer(mock_event_queue, api_key='test-key')

    def test_consumer_initialization(self, mock_event_queue):
        """Test Consumer initialization with proper attributes."""
        consumer = Consumer(mock_event_queue, api_key='test-key')

        assert consumer.running is True
        assert consumer.event_queue == mock_event_queue
        assert consumer.api_key == 'test-key'
        assert consumer._thread.daemon is True
        assert hasattr(consumer, 'http_client')

    def test_consumer_initialization_without_api_key(self, mock_event_queue):
        """Test Consumer initialization without API key."""
        consumer = Consumer(mock_event_queue)

        assert consumer.api_key is None
        assert consumer.event_queue == mock_event_queue

    @patch('src.agent_pilot.consumer.get_config')
    def test_send_batch_empty_batch(self, mock_get_config, consumer):
        """Test send_batch with empty batch does nothing."""
        mock_get_config.return_value = Mock(verbose=False)
        consumer.event_queue.get_batch.return_value = []
        consumer.http_client.post = Mock()

        consumer.send_batch()

        # Should not make any HTTP calls
        consumer.http_client.post.assert_not_called()

    @patch('src.agent_pilot.consumer.get_config')
    @patch('src.agent_pilot.consumer.logger')
    def test_send_batch_no_api_key_error(self, mock_logger, mock_get_config, consumer):
        """Test send_batch logs error when no API key is provided."""
        mock_config = Mock()
        mock_config.local_debug = False
        mock_config.api_key = None
        mock_get_config.return_value = mock_config

        consumer.api_key = None
        consumer.event_queue.get_batch.return_value = [Mock()]

        consumer.send_batch()

        mock_logger.error.assert_called_once_with('API key not found. Please provide an API key.')

    @patch('src.agent_pilot.consumer.get_config')
    @patch('src.agent_pilot.consumer.logger')
    def test_send_batch_verbose_logging(self, mock_logger, mock_get_config, consumer, mock_tracking_event):
        """Test send_batch with verbose logging enabled."""
        mock_config = Mock()
        mock_config.verbose = True
        mock_config.api_url = 'https://test-api.com'
        mock_config.api_key = 'test-api-key'
        mock_config.local_debug = False
        mock_get_config.return_value = mock_config

        consumer.event_queue.get_batch.return_value = [mock_tracking_event]
        consumer.http_client.post = Mock(return_value=('success', 200))

        consumer.send_batch()

        # Check that verbose logging occurred
        assert mock_logger.info.call_count >= 2
        mock_logger.info.assert_any_call('Sending 1 events.')
        event_data = mock_tracking_event.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude_defaults=True,
        )
        mock_logger.info.assert_any_call(f'event {mock_tracking_event.run_id}: {event_data}')

    @patch('src.agent_pilot.consumer.get_config')
    def test_send_batch_successful_request(self, mock_get_config, consumer, mock_tracking_event):
        """Test send_batch makes successful HTTP request."""
        mock_config = Mock()
        mock_config.verbose = False
        mock_config.api_url = 'https://test-api.com'
        mock_config.api_key = 'test-api-key'
        mock_config.local_debug = False
        mock_get_config.return_value = mock_config

        consumer.event_queue.get_batch.return_value = [mock_tracking_event]
        consumer.http_client.post = Mock(return_value=('success', 200))

        consumer.send_batch()

        # Verify HTTP client was called with correct parameters
        expected_data = {
            'TaskId': mock_tracking_event.task_id,
            'TrackingEvents': [mock_tracking_event.model_dump.return_value],
        }

        consumer.http_client.post.assert_called_once_with(
            action='TrackingEvent',
            data=expected_data,
            api_key='test-key',  # Consumer's API key takes precedence
            api_url='https://test-api.com',
        )

    @patch('src.agent_pilot.consumer.get_config')
    @patch('src.agent_pilot.consumer.logger')
    def test_send_batch_exception_handling(self, mock_logger, mock_get_config, consumer, mock_tracking_event):
        """Test send_batch handles exceptions properly."""
        mock_config = Mock()
        mock_config.verbose = False
        mock_config.api_url = 'https://test-api.com'
        mock_config.api_key = 'test-api-key'
        mock_config.local_debug = False
        mock_get_config.return_value = mock_config

        batch = [mock_tracking_event]
        consumer.event_queue.get_batch.return_value = batch
        consumer.http_client.post = Mock(side_effect=Exception('Network error'))

        consumer.send_batch()

        # Verify error was logged and batch was re-added to queue
        mock_logger.error.assert_called_once()
        consumer.event_queue.append.assert_called_once_with(batch)

    @patch('src.agent_pilot.consumer.get_config')
    @patch('src.agent_pilot.consumer.logger')
    def test_send_batch_exception_handling_verbose(self, mock_logger, mock_get_config, consumer, mock_tracking_event):
        """Test send_batch handles exceptions with verbose logging."""
        mock_config = Mock()
        mock_config.verbose = True
        mock_config.api_url = 'https://test-api.com'
        mock_config.api_key = 'test-api-key'
        mock_config.local_debug = False
        mock_get_config.return_value = mock_config

        batch = [mock_tracking_event]
        consumer.event_queue.get_batch.return_value = batch
        error = Exception('Network error')
        consumer.http_client.post = Mock(side_effect=error)

        consumer.send_batch()

        # Verify exception was logged with details
        mock_logger.exception.assert_called_once()
        consumer.event_queue.append.assert_called_once_with(batch)

    @patch('src.agent_pilot.consumer.get_config')
    def test_send_batch_uses_config_api_key_when_consumer_key_none(
        self, mock_get_config, mock_event_queue, mock_tracking_event
    ):
        """Test send_batch uses config API key when consumer API key is None."""
        consumer = Consumer(mock_event_queue, api_key=None)

        mock_config = Mock()
        mock_config.verbose = False
        mock_config.api_url = 'https://test-api.com'
        mock_config.api_key = 'config-api-key'
        mock_config.local_debug = False
        mock_get_config.return_value = mock_config

        consumer.event_queue.get_batch.return_value = [mock_tracking_event]
        consumer.http_client.post = Mock(return_value=('success', 200))

        consumer.send_batch()

        # Verify config API key was used
        consumer.http_client.post.assert_called_once()
        call_args = consumer.http_client.post.call_args
        assert call_args[1]['api_key'] == 'config-api-key'

    @patch('time.sleep')
    def test_run_loop(self, mock_sleep, consumer):
        """Test the run method's main loop."""
        # Mock send_batch to stop after 2 iterations
        consumer.send_batch = Mock()
        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                consumer.running = False

        consumer.send_batch.side_effect = side_effect

        consumer.run()

        # Verify send_batch was called multiple times and sleep was called
        assert consumer.send_batch.call_count >= 2
        assert mock_sleep.call_count >= 1
        mock_sleep.assert_called_with(0.5)

    def test_stop_method(self, consumer):
        """Test the stop method sets running to False."""
        consumer.running = True
        consumer._thread.is_alive = Mock(return_value=False)

        consumer.stop()

        assert consumer.running is False

    @patch('atexit.register')
    def test_atexit_registration(self, mock_atexit_register, mock_event_queue):
        """Test that _final_flush method is registered with atexit."""
        consumer = Consumer(mock_event_queue)

        mock_atexit_register.assert_called_once_with(consumer._final_flush)

    def test_consumer_has_thread(self, consumer):
        """Test that Consumer has a Thread instance."""
        assert hasattr(consumer, '_thread')
        assert isinstance(consumer._thread, Thread)
        assert consumer._thread.daemon is True

    def test_consumer_singleton(self, mock_event_queue):
        """Test that Consumer follows singleton pattern."""
        consumer1 = Consumer(mock_event_queue, api_key='key1')

        # First initialization wins
        assert consumer1.api_key == 'key1'

    @patch('src.agent_pilot.consumer.get_config')
    def test_send_batch_local_debug_mode(self, mock_get_config, consumer, mock_tracking_event):
        """Test send_batch works in local debug mode without API key."""
        mock_config = Mock()
        mock_config.verbose = False
        mock_config.api_url = 'https://test-api.com'
        mock_config.api_key = 'test-key'
        mock_config.local_debug = True
        mock_get_config.return_value = mock_config

        consumer.api_key = None
        consumer.event_queue.get_batch.return_value = [mock_tracking_event]
        consumer.http_client.post = Mock(return_value=('success', 200))

        consumer.send_batch()

        # Should proceed with HTTP call even without API key in debug mode
        consumer.http_client.post.assert_called_once()

    def test_final_flush_prevents_data_loss(self, mock_event_queue, mock_tracking_event):
        """Test that _final_flush properly sends remaining events on exit."""
        consumer = Consumer(mock_event_queue)

        # Mock the send_batch method to track calls
        consumer.send_batch = Mock()

        # Simulate some events in queue
        mock_event_queue.get_batch.return_value = [mock_tracking_event]

        # Call _final_flush (simulating process exit)
        consumer._final_flush()

        # Verify that running is set to False
        assert consumer.running is False

        # Verify that send_batch was called to flush remaining events
        consumer.send_batch.assert_called_once()

    def test_final_flush_handles_exceptions(self, mock_event_queue):
        """Test that _final_flush handles exceptions gracefully."""
        consumer = Consumer(mock_event_queue)

        # Mock send_batch to raise an exception
        consumer.send_batch = Mock(side_effect=Exception('Network error'))

        # _final_flush should not raise an exception
        try:
            consumer._final_flush()
        except Exception:
            pytest.fail('_final_flush should handle exceptions gracefully')

        # Verify that running is still set to False even with exception
        assert consumer.running is False

    @patch('src.agent_pilot.consumer.logger')
    def test_final_flush_with_actual_events(self, mock_logger, mock_event_queue, mock_tracking_event):
        """Test that _final_flush actually processes events from the queue."""
        consumer = Consumer(mock_event_queue)

        # Set up queue to return some events
        mock_event_queue.get_batch.return_value = [mock_tracking_event, mock_tracking_event]

        # Mock config and HTTP client for send_batch
        with patch('src.agent_pilot.consumer.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.verbose = False
            mock_config.api_url = 'https://test-api.com'
            mock_config.api_key = 'test-key'
            mock_config.local_debug = False
            mock_get_config.return_value = mock_config

            consumer.http_client.post = Mock(return_value=('success', 200))

            # Call _final_flush
            consumer._final_flush()

            # Verify that events were processed
            mock_event_queue.get_batch.assert_called_once()
            consumer.http_client.post.assert_called_once()

            # Verify that running is set to False
            assert consumer.running is False

    def test_data_loss_prevention_scenario(self, mock_event_queue, mock_tracking_event):
        """Test a realistic scenario where final flush prevents data loss."""
        consumer = Consumer(mock_event_queue)

        # Simulate events that would be lost without final flush
        pending_events = [mock_tracking_event for _ in range(5)]
        mock_event_queue.get_batch.return_value = pending_events

        # Mock successful HTTP sending
        with patch('src.agent_pilot.consumer.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.verbose = False  # Disable verbose to avoid logging issues
            mock_config.api_url = 'https://test-api.com'
            mock_config.api_key = 'test-key'
            mock_config.local_debug = False
            mock_get_config.return_value = mock_config

            consumer.http_client.post = Mock(return_value=('success', 200))

            # Simulate process exit - this should save all pending events
            consumer._final_flush()

            # Verify all events were processed
            mock_event_queue.get_batch.assert_called_once()

            # Verify HTTP call was made
            consumer.http_client.post.assert_called_once()

            # Verify HTTP call was made with correct parameters
            call_args = consumer.http_client.post.call_args
            assert 'action' in call_args[1]
            assert call_args[1]['action'] == 'TrackingEvent'
            assert 'data' in call_args[1]
            assert 'TrackingEvents' in call_args[1]['data']
            assert len(call_args[1]['data']['TrackingEvents']) == 5  # All 5 events sent

            # Consumer should be stopped
            assert consumer.running is False
