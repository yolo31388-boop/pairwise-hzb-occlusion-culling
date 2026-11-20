import pytest
from render import hzb_occlusion_culling as mod

CASES = [
    ("expand", 'm.expand_bounds((0, 0, 10, 10), (2, 3)) == (-2, -3, 12, 13)'),
    ("mip", 'm.mip_rect((0, 0, 8, 8), 1) == (0, 0, 4, 4)'),
    ("depth", 'm.depth_compare(False, 1, 2) is True'),
    ("key", 'm.camera_hzb_key("L") == "L"'),
    ("barrier", 'm.barrier_needed("hzb", "cull") is True'),
    ("near", 'm.near_clip_guard((0, 0, 10, 10), 5) is True'),
    ("transparent", 'm.transparent_occluder(0.8) is True'),
    ("instance", 'm.instance_bounds((0, 0, 5, 5), (2, 3)) == (2, 3, 7, 8)'),
    ("buffer", 'm.double_buffer("a", "b") == ("b", "a")'),
    ("expand2", 'm.conservative_expand((0, 0, 10, 10), 2) == (-2, -2, 12, 12)'),
    ("levels", 'm.hzb_level_count(8, 8) == 4'),
    ("occlusion", 'm.occlusion_result(False, True) is True'),
    ("mipsel", 'm.mip_select(8, 2) == 2'),
    ("batch", 'm.cull_batch([True, False, True]) == 2'),
    ("throttle", 'm.readback_throttle(0, 2) is True')
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx})
