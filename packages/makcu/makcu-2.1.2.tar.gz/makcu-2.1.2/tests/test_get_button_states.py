# test_get_button_states.py
import time
from makcu import MouseButton

def test_get_button_states(makcu):
    time.sleep(3)
    assert makcu.is_button_pressed(MouseButton.LEFT)