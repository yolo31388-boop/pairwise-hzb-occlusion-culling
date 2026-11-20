import math

def expand_bounds(bounds, motion):
    """运动扩张包围盒。"""
    raise NotImplementedError("TODO: expand_bounds")

def mip_rect(rect, level):
    """mip 矩形。"""
    raise NotImplementedError("TODO: mip_rect")

def depth_compare(reverse_z, a, b):
    """深度比较。"""
    raise NotImplementedError("TODO: depth_compare")

def camera_hzb_key(camera_id):
    """多相机 HZB 键。"""
    raise NotImplementedError("TODO: camera_hzb_key")

def barrier_needed(producer, consumer):
    """HZB barrier。"""
    raise NotImplementedError("TODO: barrier_needed")

def near_clip_guard(bounds, near):
    """近平面保护。"""
    raise NotImplementedError("TODO: near_clip_guard")

def transparent_occluder(alpha):
    """透明遮挡写入。"""
    raise NotImplementedError("TODO: transparent_occluder")

def instance_bounds(bounds, offset):
    """实例包围盒。"""
    raise NotImplementedError("TODO: instance_bounds")

def double_buffer(active, next_buffer):
    """结果双缓冲。"""
    raise NotImplementedError("TODO: double_buffer")

def conservative_expand(rect, pixels):
    """保守膨胀。"""
    raise NotImplementedError("TODO: conservative_expand")

def hzb_level_count(width, height):
    """HZB 层数。"""
    raise NotImplementedError("TODO: hzb_level_count")

def occlusion_result(visible, conservative):
    """遮挡结果。"""
    raise NotImplementedError("TODO: occlusion_result")

def mip_select(bounds_size, texel):
    """mip 选择。"""
    raise NotImplementedError("TODO: mip_select")

def cull_batch(visible_flags):
    """批量剔除计数。"""
    raise NotImplementedError("TODO: cull_batch")

def readback_throttle(frame, interval):
    """回读节流。"""
    raise NotImplementedError("TODO: readback_throttle")
