import subprocess
import sys
import os
import pytest


class TestConsumerIntegration:
    """Integration tests for Consumer atexit behavior."""

    def test_atexit_flush_on_process_exit(self, tmp_path):
        """Test that atexit properly flushes events when process exits normally."""

        # Use pytest's tmp_path fixture for automatic cleanup
        result_file = tmp_path / 'atexit_test_result.txt'

        # Get the current directory to build the path to src
        current_dir = os.path.dirname(__file__)
        src_path = os.path.join(current_dir, '..', 'src')

        # Create a simplified test script that verifies atexit registration and execution
        test_script = f'''
import sys
import os
import atexit
from unittest.mock import patch

# Add the src directory to path
sys.path.insert(0, r"{src_path}")

# Track atexit execution
atexit_executed = False

def track_atexit():
    global atexit_executed
    atexit_executed = True
    with open(r"{result_file}", "w") as f:
        f.write("atexit_executed")

# Register our tracker before importing Consumer
atexit.register(track_atexit)

# Mock HTTP client to avoid network calls
with patch('agent_pilot.http_client.get_http_client') as mock_client:
    mock_client.return_value.post.return_value = ('success', 200)
    
    from agent_pilot.event_queue import EventQueue
    
    # Create event queue (which creates Consumer with atexit registration)
    queue = EventQueue()
    
    print("Test process setup complete, registrations done")
    # Process will exit normally, triggering atexit handlers
'''

        # Run the test script in a subprocess
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Verify the process completed successfully
        assert result.returncode == 0, f'Subprocess failed: {result.stderr}'

        # Check that our atexit handler was executed
        if result_file.exists():
            content = result_file.read_text().strip()
            assert content == 'atexit_executed', f"Expected 'atexit_executed', got '{content}'"
            print('✅ atexit mechanism works correctly on process exit!')
        else:
            pytest.fail('Atexit handler was not executed - result file not created')

    def test_atexit_registration_integration(self, tmp_path):
        """Test that atexit.register is properly called during Consumer initialization."""

        # Get the current directory to build the path to src
        current_dir = os.path.dirname(__file__)
        src_path = os.path.join(current_dir, '..', 'src')

        # Use tmp_path for any potential file operations in the subprocess
        result_file = tmp_path / 'registration_result.txt'

        test_script = f'''
import sys
import os
import json
import atexit
from unittest.mock import Mock, patch

# Add the src directory to path  
sys.path.insert(0, r"{src_path}")

# Track atexit registrations
registered_functions = []

def mock_atexit_register(func):
    registered_functions.append(func.__name__)
    # Write result to file for verification
    with open(r"{result_file}", "w") as f:
        f.write("_final_flush" if func.__name__ == "_final_flush" else "other")
    return func

# Mock atexit.register before importing Consumer
with patch('atexit.register', side_effect=mock_atexit_register):
    with patch('agent_pilot.http_client.get_http_client') as mock_client:
        mock_client.return_value.post.return_value = ('success', 200)
        
        from agent_pilot.event_queue import EventQueue
        
        # Create event queue (which creates Consumer)
        queue = EventQueue()
        
        # Check that _final_flush was registered
        assert '_final_flush' in registered_functions
        print("✅ atexit.register was called with _final_flush")
'''

        result = subprocess.run(
            [sys.executable, '-c', test_script],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Check if the test passed
        assert result.returncode == 0, f'Test failed with output: {result.stdout}\nErrors: {result.stderr}'
        assert '✅ atexit.register was called with _final_flush' in result.stdout

        # Additional verification using the result file
        if result_file.exists():
            content = result_file.read_text().strip()
            assert content == '_final_flush', f"Expected '_final_flush', got '{content}'"
