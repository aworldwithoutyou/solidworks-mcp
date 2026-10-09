---
name: solidworks-cad
description: AI 辅助 SolidWorks 工程作图工作流：用 solidworks MCP 工具参数化建模、出工程图、批量改参导出。
---

# SolidWorks AI 辅助工程作图

本技能教你如何用 `solidworks` MCP 服务器（38 个 `sw_*` 工具）驱动本机 SolidWorks 完成工程作图。所有工具都通过一个常驻会话串行执行。

## 核心约定

- **单位**：所有长度一律用**毫米 (mm)**（内部已转换为 SolidWorks 的米）。角度用度。
- **必须先 `sw_connect`**：拿到 `revision`（应为 `30.x`）后再操作。
- **每一步都核对**：建模后调 `sw_mass_properties` 核对体积/质量，或 `sw_screenshot` 截图回看（截图路径要在系统临时目录）。
- **平面名用中文**：`front` / `top` / `right` 已映射到「前视基准面 / 上视基准面 / 右视基准面」，也兼容英文。
- **视图名**：工程图用 `front` / `top` / `right` / `left` / `isometric` 等（已映射到中文 `*前视`/`*上视`/`*右视`/`*等轴测`）。
- **稳定性铁律**：每次 `sw_new_part` 后必须 `sw_close`，别堆积文档窗口——十几个未关窗口会把 SolidWorks 拖到无响应甚至崩溃（只能 `taskkill /F /IM SLDWORKS.exe` 重启）。

## 常用工作流

### 1. 参数化零件建模
1. `sw_new_part` → 得到标题。
2. `sw_sketch_rectangle("front", -50, -30, 50, 30)` 或 `sw_sketch_circle(plane, cx, cy, r)`。
3. `sw_extrude(8.0)`（深度 mm；通孔用 `sw_extrude_cut`，默认贯穿）。
4. 圆角 `sw_fillet`、倒角 `sw_chamfer`、抽壳 `sw_shell`、阵列 `sw_linear_pattern`/`sw_circular_pattern`、镜像 `sw_mirror`、打孔 `sw_hole_wizard`。
5. `sw_rebuild` 后 `sw_mass_properties` 核对体积，`sw_screenshot` 回看。

**尺寸参数名**：改尺寸用 `sw_set_parameter("D1@凸台-拉伸1", 12.0)`（格式 `D1@<特征名>`，特征名如「凸台-拉伸1」「切除-拉伸1」）。先用 `sw_get_parameter` 读确认存在。

### 2. 出 2D 工程图
1. 先把零件 `sw_save(<路径>.sldprt)`。
2. `sw_new_drawing` → `sw_create_view(<零件路径>, "front", x, y)` 插入前/上/右/等轴测视图。
3. `sw_insert_annotations` 插入模型尺寸标注。
4. `sw_export(<路径>.pdf)` 导出 PDF（或 .dwg）。

### 3. 批量改参导出
1. `sw_open(<路径>.sldprt, "part")`。
2. 循环 `sw_set_parameter(name, 新值)` + `sw_rebuild`。
3. `sw_export_document(<路径>.step)` 导出 STEP（或 .pdf/.dxf）。

## 工具速查

- 会话：`sw_connect` `sw_version` `sw_new_part` `sw_open` `sw_save` `sw_close` `sw_list_documents` `sw_screenshot`
- 选择：`sw_select` `sw_clear_selection`
- 草图：`sw_sketch_rectangle` `sw_sketch_circle`
- 特征：`sw_extrude` `sw_extrude_cut` `sw_revolve` `sw_fillet` `sw_chamfer` `sw_shell` `sw_linear_pattern` `sw_circular_pattern` `sw_mirror` `sw_hole_wizard`
- 检查：`sw_rebuild` `sw_mass_properties`
- 工程图：`sw_new_drawing` `sw_create_view` `sw_insert_annotations` `sw_export`
- 装配体：`sw_new_assembly` `sw_add_component` `sw_add_mate` `sw_interference_check` `sw_create_exploded_view` `sw_add_explode_step`（注：配合/干涉计数受 SolidWorks COM 绑定限制，可能返回空）
- 批量：`sw_get_parameter` `sw_set_parameter` `sw_export_document`

## 备用通道：MCP 被禁用时直驱 Python API

若 `sw_*` 工具报 `disabled in this session` 或连不上，直接驱动同项目 Python API（与 sw_* 同一套实现）：

- 解释器：`<项目>\.venv\Scripts\python.exe`；运行：`cd <项目> && ./.venv/Scripts/python.exe build.py`
- 入口：`from solidworks_mcp import runtime`
- **铁律**：所有 COM 调用必须在 STA worker 线程内，用 `sess.worker.call(fn)` 或 `modeling/drawing/...` 封装方法；**不可嵌套 `worker.call`**（封装方法内部已排队，再套一层会死锁）。

### 自包含脚本模板（只开一个文档，跑完即关）

```python
import sys, os
sys.path.insert(0, r"<项目>")
import pythoncom
from win32com.client import VARIANT
from solidworks_mcp import runtime

MM = 0.001
def callout():  return VARIANT(pythoncom.VT_DISPATCH, None)

def close_all():
    sw = runtime.get_session().require_sw()
    docs = sw.GetDocuments; docs = docs() if callable(docs) else docs
    for d in list(docs or ()):
        try: d.SetSaveFlag()
        except Exception: pass
        t = d.GetTitle; t = t() if callable(t) else t
        sw.CloseDoc(t)

def build():                       # 整个 COM 序列跑在 worker STA 线程内
    sw  = runtime.get_session().require_sw()
    doc = sw.ActiveDoc
    sm, fm = doc.SketchManager, doc.FeatureManager
    doc.Extension.SelectByID2("前视基准面", "PLANE", 0,0,0, False,0,callout(),0)
    sm.InsertSketch(True)
    sm.CreateCornerRectangle(-50*MM,-30*MM,0, 50*MM,30*MM,0)   # 或 CreateSpline2 见下
    sm.InsertSketch(True)
    fm.FeatureExtrusion3(True,False,False,0,0,20*MM,0,
        False,False,False,False,0,0, False,False,False,False,
        True,True,True, 0,0,False)
    doc.ShowNamedView2("等轴测", 7); doc.ViewZoomtofit2()
    return len(doc.GetBodies2(0, True) or ())

def main():
    sess = runtime.get_session(visible=True)
    sess.connect()
    sess.worker.call(close_all)                 # 清理旧窗口
    sess.new_document("part")
    print("bodies:", sess.worker.call(build))
    sess.save(r"C:\out\part.sldprt")
    sess.save_screenshot(r"C:\out\preview.png")
    sess.close()                                # 关掉，别堆积
    runtime.shutdown()

main()
```

### 闭合样条轮廓（光滑，避免折线「灯笼棱」）

```python
flat = [c for (x, y) in pts + [pts[0]] for c in (x*MM, y*MM, 0.0)]  # 首尾同点 = 闭合
sm.CreateSpline2(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat), False)
```

### 面着色（9 元素，transparency 必须在第 8 位）

```python
arr = [r, g, b, 0.55, 0.88, 0.25, 0.45, 0.0, 0.0]   # 末尾 0.0 = 不透明
face.SetMaterialPropertyValues2(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, arr), 1, None)
doc.GraphicsRedraw2()                                # 必须刷新才生效
```

## 关键 API 与实战踩坑

- **草图**：`CreateLine` / `CreateSpline2` / `CreateCircleByRadius` / `CreateCornerRectangle` / `CreateCenterLine` + `InsertSketch`（进入/退出）。
- **特征**：`FeatureExtrusion3`（第 18 参 `Merge` 设 False 可让某特征成为独立实体，方便整块上色）；`FeatureRevolve2`（需闭合剖面 + 中心线，剖面两端点要落在中心线上，auto-select 靠草图中心线当轴）；`FeatureFillet3`。
- **查询/刷新**：`GetBodies2` / `GetMassProperties` / `GetEdges` / `Extension.SelectByID2`；`ShowNamedView2("等轴测",7)` + `ViewZoomtofit2()`；`GraphicsRedraw2()`；`ForceRebuild3(False)`（`EditRebuild3` 是属性不是方法）。
- **选边**：`edge.Select4(True, VARIANT(VT_DISPATCH, None))`（不能直接传 None）；样条拉伸体边极少（2 条端面边）可 `body.GetEdges()` 全选再 `FeatureFillet3`；折线体用 `SelectByID2("", "EDGE", x, y, z, True, 0, callout, 0)` 按段中点 + 两个 z 面选边。
- **圆角半径分档递减重试**（52→46→40→32→24）：一次给太大会留「帽檐」面甚至直接失败（返回 None）。
- **着色**：`SetMaterialPropertyValues2` 的 9 元素数组若多填 RGB，会把多余通道当 transparency → 模型半透明（能看到内部边线）；第 8 位 transparency=0.0 才不透明。改完必须 `GraphicsRedraw2()`。
- **轮廓自交**（如尾叉等凹形）→ 拉伸静默失败（FeatureExtrusion3 返回 None、bodies=0）；设计点序务必保证简单多边形。
- **早期绑定不可用**：`gencache.EnsureDispatch` 报「找不到元素/无法 makepy」；`FirstFeature` 等 vtable-only 成员在 late-binding 下不可用。

## 已知限制

- 装配体的配合(`sw_add_mate`)、干涉计数、爆炸步骤依赖 SolidWorks vtable-only 接口，pywin32 无法自动 early-bind，可能不生效。
- 工程图自动尺寸/GD&T 标注能力受 SolidWorks API 限制，复杂标注仍需手工。
- `EnsureDispatch`、`FirstFeature`、顶点坐标查询（late-binding 下 vtable-only 不可用）。
- 若 SolidWorks 未运行，首次 `sw_connect` 会启动它（较慢）。
