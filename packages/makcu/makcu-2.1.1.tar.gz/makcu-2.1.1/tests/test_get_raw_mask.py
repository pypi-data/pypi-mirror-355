# test_get_raw_mask.py

def test_get_raw_mask(makcu):
    mask = makcu.get_raw_mask()
    assert isinstance(mask, int)