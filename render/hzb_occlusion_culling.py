"""HZB（Hierarchical Z-Buffer）遮挡剔除的辅助实现。

这里的每个函数都对应一类线上事故的修复要点，注释里写明了它为什么必须保守：

* 运动扩张        —— HZB 来自上一帧，相机移动后包围盒的屏幕位置会漂移；
* mip 选择        —— 按屏幕矩形而不是包围盒中心选层，避免边缘闪烁；
* 深度约定        —— 反向 Z / 普通 Z 的比较方向必须统一；
* 多相机 HZB      —— 左眼 / 右眼 / 分屏各自一张，禁止共享；
* barrier         —— compute 写 HZB 与 culling 读之间必须有内存屏障；
* 近平面保护      —— 任何被近平面裁到的物体都按可见处理；
* 透明不写遮挡    —— 非全不透明表面不进入 HZB；
* 实例级 bounds   —— 实例化物体按每个实例自己的包围盒测试；
* 结果双缓冲      —— 本帧结果写 next，读取 active，避免 readback 阻塞；
* 保守膨胀        —— 降分辨率后的 HZB 覆盖范围要向外膨胀。
"""

import math


def _pair(value):
    """把标量或二元组统一成 (x, y) 形式，保持原有的数值类型。"""
    if isinstance(value, (tuple, list)):
        if len(value) == 1:
            return value[0], value[0]
        return value[0], value[1]
    return value, value


def expand_bounds(bounds, motion):
    """按相机运动扩张包围盒（运动模糊式的保守扩张）。

    ``bounds`` 是屏幕空间矩形 ``(x0, y0, x1, y1)``，``motion`` 是本帧相对
    HZB 所在帧的运动量（标量或 ``(mx, my)``）。HZB 的深度是上一帧的，快速
    横移时物体在新帧的屏幕位置已经偏移，必须沿运动方向双向扩张，否则整个
    物体可能落在旧 HZB 的覆盖范围之外而被误剔除。
    """
    x0, y0, x1, y1 = bounds
    mx, my = _pair(motion)
    mx, my = abs(mx), abs(my)
    return (x0 - mx, y0 - my, x1 + mx, y1 + my)


def mip_rect(rect, level):
    """包围盒在 ``level`` 级 mip 上对应的矩形。

    HZB 每升一级宽高减半。按矩形而不是按中心点选层：用矩形可以保证覆盖
    物体在屏幕上的全部投影，边缘物体不会在阈值附近来回跳变。
    """
    x0, y0, x1, y1 = rect
    factor = 1 << max(0, int(level))
    width = max(1, (x1 - x0) // factor)
    height = max(1, (y1 - y0) // factor)
    return (x0, y0, x0 + width, y0 + height)


def depth_compare(reverse_z, a, b):
    """判断 ``a`` 是否比 ``b`` 更靠近相机，遵循统一后的深度约定。

    * 普通 Z：深度值越小越近，``a < b``；
    * 反向 Z：深度值越大越近，``a > b``。

    两种约定混用会让比较方向整体反转，遮挡关系随之颠倒。
    """
    return a > b if reverse_z else a < b


def camera_hzb_key(camera_id):
    """每台相机（左眼 / 右眼 / 分屏视口）各自的 HZB 键。

    多相机共享一张 HZB 会让不同投影下的深度互相污染，左右眼剔除结果不一致。
    """
    return str(camera_id)


def barrier_needed(producer, consumer):
    """生产者阶段与消费者阶段之间是否需要插入内存屏障。

    异步 compute 生成 HZB 后，culling 的采样必须看到已完成的写入；只要两个
    阶段不同，就需要屏障，否则会出现偶发漏画。
    """
    return str(producer).strip().lower() != str(consumer).strip().lower()


def near_clip_guard(bounds, near):
    """近平面保护：返回 True 表示该物体必须按可见处理。

    取包围盒各分量中的最小值作为物体最靠近相机的深度。只要它没有严格位于
    近平面之后，物体就可能被近平面裁切或投影不稳定，此时不能信任 HZB 的
    深度测试，一律保守地保留。
    """
    if not bounds:
        return True
    depth_min = min(bounds)
    return depth_min <= near


def transparent_occluder(alpha):
    """透明表面是否应被排除在遮挡写入之外。

    返回 True 表示该表面不是全不透明，不能写入 HZB，否则它后面的不透明
    物体会被错误剔除。
    """
    return alpha < 1.0 - 1e-6


def instance_bounds(bounds, offset):
    """实例化物体的单个实例包围盒（整体 bounds 按实例偏移平移）。

    实例化网格只测整体 bounds 会漏掉实例之间的大量空白区域，必须对每个
    实例分别做遮挡测试。
    """
    x0, y0, x1, y1 = bounds
    ox, oy = _pair(offset)
    return (x0 + ox, y0 + oy, x1 + ox, y1 + oy)


def double_buffer(active, next_buffer):
    """交换双缓冲，返回 ``(新 active, 新 next)``。

    本帧剔除写入 next，同时继续读取上一帧的 active，避免 GPU readback
    阻塞主线程。
    """
    return (next_buffer, active)


def conservative_expand(rect, pixels):
    """把矩形向四周膨胀 ``pixels`` 个像素。

    性能档降低 HZB 分辨率后，单个 texel 覆盖更多像素，边界处的遮挡信息
    不确定，必须向外保守膨胀，否则边缘物体会闪烁。
    """
    x0, y0, x1, y1 = rect
    pixels = max(0, int(pixels))
    return (x0 - pixels, y0 - pixels, x1 + pixels, y1 + pixels)


def hzb_level_count(width, height):
    """HZB 的 mip 层数，包含最底层的全分辨率。

    8x8 的深度图依次得到 8、4、2、1，共 4 层。
    """
    if width <= 0 or height <= 0:
        return 0
    return int(math.floor(math.log2(min(width, height)))) + 1


def occlusion_result(visible, conservative):
    """合并遮挡测试结果。

    ``conservative`` 表示本次测试是在保守条件下做的（例如 mip 覆盖范围
    有歧义），此时即使判定为不可见也要保留，宁可多画不可漏画。
    """
    return bool(visible or conservative)


def mip_select(bounds_size, texel):
    """按屏幕矩形尺寸选择 mip 层级。

    选择使一个 texel 不大于包围盒尺寸的最高层：``floor(log2(size / texel))``。
    尺寸不大于单个 texel 时取第 0 层。
    """
    if texel <= 0 or bounds_size <= 0:
        return 0
    ratio = float(bounds_size) / float(texel)
    if ratio <= 1.0:
        return 0
    return int(math.floor(math.log2(ratio)))


def cull_batch(visible_flags):
    """统计一批物体的可见数量。"""
    return sum(1 for flag in visible_flags if flag)


def readback_throttle(frame, interval):
    """回读节流：仅每隔 ``interval`` 帧回读一次结果，返回本帧是否回读。

    ``interval <= 1`` 时每帧都回读。
    """
    if interval <= 1:
        return True
    return frame % interval == 0
