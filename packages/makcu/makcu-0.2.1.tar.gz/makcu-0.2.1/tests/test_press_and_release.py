# test_press_and_release.py

from makcu import MouseButton

def test_press_and_release(makcu):
    makcu.press(MouseButton.LEFT)
    makcu.release(MouseButton.LEFT)