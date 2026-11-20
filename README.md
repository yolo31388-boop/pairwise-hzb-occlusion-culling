# pairwise-hzb-occlusion-culling

GPU 遮挡剔除在相机快速横移时把整栋楼剔掉，HZB 用的是上一帧深度，没按相机运动扩张包围盒；mip 选择按包围盒中心，边缘物体在阈值上反复闪烁；反向 Z 与普通 Z 约定混用，深度比较方向反了；多相机分屏共享一张 HZB，左右眼剔除结果不同；异步 compute 生成 HZB 与 culling 读之间没有 barrier，偶发漏画；小物体包围盒被近平面裁掉，错误判定为不可见；透明物体参与遮挡写入，后面的不透明物体被剔；实例化物体只测整体 bounds，单个实例漏剔除；剔除结果没有双缓冲，GPU readback 阻塞主线程；性能档降低 HZB 分辨率却没做保守扩张，边缘物体闪烁。render/hzb_occlusion_culling.py 是核心，tests/test_hzb_occlusion_culling.py 15个红。要修的是：包围盒按运动扩张；mip 按屏幕矩形选；统一深度约定；多相机独立 HZB；compute 后插 barrier；近平面保守裁剪；透明不写遮挡；实例级 bounds；结果双缓冲；降分辨率加保守膨胀。

## 运行

```bash
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。

子方向：见平台；任务类型：Bugfix；语言/框架：Python 3, pytest；环境可复现等级：无外部依赖。
