import pytest
import subprocess
import time

@pytest.fixture(scope="session", autouse=True)
def mqtt_broker():
    """Ensure MQTT broker is running for tests."""
    # Check if mosquitto is running
    try:
        # You might need to adjust this command based on your OS
        subprocess.run(["pgrep", "mosquitto"], check=True)
    except subprocess.CalledProcessError:
        pytest.skip("Mosquitto broker is not running. Please start it before running tests.")
    
    # Wait for broker to be ready
    time.sleep(1) 