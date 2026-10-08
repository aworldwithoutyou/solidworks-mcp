---
name: solidworks-cad
description: AI 辅助 SolidWorks 工程作图工作流：用 solidworks MCP 工具参数化建模、出工程图、批量改参导出。
---

# SolidWorks AI 辅助工程作图

本技能教你如何用 `solidworks` MCP 服务器（38 个 `sw_*` 工具）驱动本机 SolidWorks 2022 完成工程作图。所有工具都通过一个常驻会话串行执行。

## 核心约定

- **单位**：所有长度一律用**毫米 (mm)**（内部已转换为 SolidWorks 的米）。角度用度。
- **必须先 `sw_connect`**：拿到 `revision`（应为 `30.x`）后再操作。
- **每一步都核对**：建模后调 `sw_mass_properties` 核对体积/质量，或 `sw_screenshot` 截图回看（截图路径要在系统临时目录）。
- **平面名**：用 `front` / `top` / `right`（已映射到中文基准面「前视/上视/右视基准面」，也兼容英文）。
- **视图名**：工程图用 `front` / `top` / `right` / `left` / `isometric` 等（已映射到中文 `*前视`/`*上视`/`*右视`/`*等轴测`）。

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

## 已知限制

- 装配体的配合(`sw_add_mate`)、干涉计数、爆炸步骤依赖 SolidWorks vtable-only 接口，pywin32 无法自动 early-bind，可能不生效。
- 工程图自动尺寸/GD&T 标注能力受 SolidWorks API 限制，复杂标注仍需手工。
- 若 SolidWorks 未运行，首次 `sw_connect` 会启动它（较慢）。
