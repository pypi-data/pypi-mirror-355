# test_is_button_pressed.py

from makcu import MouseButton

def test_is_button_pressed(makcu):
    assert makcu.is_button_pressed(MouseButton.LEFT) in [True, False]