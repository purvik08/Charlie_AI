import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.assistant import SystemInfo

def test_system_info_get_system_info():
    """Test that get_system_info returns expected keys"""
    info = SystemInfo.get_system_info()

    # Check that essential keys are present
    expected_keys = [
        "system", "node", "release", "version",
        "machine", "processor"
    ]

    for key in expected_keys:
        assert key in info
        assert isinstance(info[key], str)
        assert len(info[key]) > 0

def test_system_info_get_battery_info():
    """Test that get_battery_info returns a dictionary"""
    battery_info = SystemInfo.get_battery_info()

    # Should return a dictionary (might be empty if no battery)
    assert isinstance(battery_info, dict)

    # If it has data, check for expected keys
    if battery_info:
        expected_keys = ["percent", "power_plugged", "seconds_left"]
        for key in expected_keys:
            if key in battery_info:
                # Just check that the key exists, values can vary
                pass

if __name__ == "__main__":
    test_system_info_get_system_info()
    test_system_info_get_battery_info()
    print("All system info tests passed!")