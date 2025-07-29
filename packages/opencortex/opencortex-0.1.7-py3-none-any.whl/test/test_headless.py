"""
Test StreamEngine running without GUI
"""

import time
import yaml
from brainflow.board_shim import BoardShim, BrainFlowInputParams

from opencortex.neuroengine.core.stream_engine import HeadlessStreamEngine

# Load your config
with open('default_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Initialize board (use synthetic for testing)
params = BrainFlowInputParams()
board = BoardShim(-1, params)  # Synthetic board

# Create headless engine
engine = HeadlessStreamEngine(board, config)


# Add monitoring
def data_monitor(data):
    print(f"Data: {data.timestamp}, Quality: {len(data.quality_scores)} channels")


def event_monitor(event_type, data):
    print(f"Event: {event_type} - {data}")


engine.register_data_callback(data_monitor)
engine.register_event_callback(event_monitor)

# Start streaming
board.prepare_session()
board.start_stream()

print("Starting headless StreamEngine...")
engine.start()

try:
    # Run for 30 seconds
    time.sleep(30)

    # Send some test commands
    engine.send_command('send_trigger', {'trigger': 1})
    time.sleep(5)

    engine.send_command('set_inference_mode', {'mode': True})
    time.sleep(5)

except KeyboardInterrupt:
    print("Interrupted")
finally:
    engine.stop()
    board.stop_stream()
    board.release_session()
    print("Headless test complete")