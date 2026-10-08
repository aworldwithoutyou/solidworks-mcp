#注意 本文件全程由ai设计编写
# solidworks-mcp

本地 MCP 服务器，把 Reasonix（或任意 MCP 客户端）接入本机 SolidWorks，实现 AI 辅助工程作图：参数化零件建模、2D 工程图出图、装配体、批量改参导出。

## 环境要求

- Windows + SolidWorks（本项目在 SolidWorks 2022 SP05 上实测，理论兼容 2018+）
- Python 3.10+

## 安装

```powershell
# 在项目根目录执行
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

依赖随包自动安装：`pywin32`、`mcp`（2.x）。

## 配置（可选）

无需配置即可工作——程序会自动探测 SolidWorks 安装目录与模板目录。若你的安装位置不标准，可用环境变量显式指定：

| 变量 | 作用 |
| --- | --- |
| `SOLIDWORKS_TEMPLATES_DIR` | 模板目录（含 `gb_part.prtdot` / `gb_assembly.asmdot` / `gb_a*.drwdot`） |
| `SOLIDWORKS_INSTALL_DIR` | SolidWorks 安装根目录（含 `sldworks.tlb` / `SLDWORKS.exe`） |
| `SOLIDWORKS_MCP_GENPY` | win32com 早绑定缓存目录（默认项目下 `gen_py/`） |

## 接入 Reasonix

以 stdio 服务器 `solidworks` 注册，`command` 指向你本机 venv 的 python：

```toml
# reasonix.toml
[[mcp.servers]]
name = "solidworks"
command = "<项目目录>\\.venv\\Scripts\\python.exe"
args = ["-m", "solidworks_mcp.server"]
```

项目根已附 `.mcp.json`（标准格式），把其中 `command` 改成你的 venv 路径即可。

配套技能手册在 `skills/solidworks-cad/SKILL.md`：复制到 Reasonix 的技能目录后，用 `/solidworks-cad` 调用即可让 AI 按工程制图规范操作这些工具。

## 使用方式

在 Reasonix 会话里直接说需求，例如：

> 帮我画一块 100×60×8 的板，四角开 φ6 通孔，边缘 2mm 倒角，然后出三视图工程图导出 PDF。

Reasonix 会调用 `sw_*` 工具完成建模、截图自检、出图、导出。38 个工具按职责分组：

- 会话/文档：`sw_connect` `sw_new_part` `sw_open` `sw_save` `sw_close` `sw_screenshot` …
- 草图/特征：`sw_sketch_rectangle` `sw_sketch_circle` `sw_extrude` `sw_extrude_cut` `sw_fillet` `sw_chamfer` `sw_hole_wizard` …
- 检查：`sw_rebuild` `sw_mass_properties`
- 工程图：`sw_new_drawing` `sw_create_view` `sw_insert_annotations` `sw_export`
- 装配体：`sw_new_assembly` `sw_add_component` `sw_add_mate` `sw_interference_check` `sw_create_exploded_view` …
- 批量：`sw_get_parameter` `sw_set_parameter` `sw_export_document`

## 运行测试

需要 SolidWorks 在运行（首次 `sw_connect` 会自动启动它）：

```powershell
.\.venv\Scripts\python.exe scripts\cleanup_sw.py          # 清理未保存文档
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## 架构

```
solidworks_mcp/
  com/worker.py          # 单一 STA 线程，串行化所有 COM 调用
  com/session.py         # 连接/模板解析/文档管理
  com/gencache_bootstrap.py  # 固定 early-binding 缓存目录
  config.py              # 路径/常量集中管理 + 自动探测
  modeling.py            # 草图 + 特征
  drawing.py             # 工程图
  assembly.py            # 装配体
  batch.py               # 批量改参 + 导出
  server.py              # MCP 工具定义（38 个 sw_*）
  runtime.py             # 共享会话单例
```

## 已知限制

- **装配体配合/干涉计数/爆炸步骤**：SolidWorks 把 `AddMate3`、`GetInterferenceCount`、`AddExplodeStep` 等放在 vtable-only 接口，pywin32 无法对 SolidWorks 自动 early-bind，这些操作可能返回空。插入零件、爆炸视图创建已验证可用；配合/干涉需改用 VBA 宏或 .NET 方案。
- **工程图自动 GD&T 标注**：受 SolidWorks Drawing API 限制，只能插入已有模型尺寸，全新几何公差标注仍需手工。
- **尺寸参数名**：需按 `D1@<特征名>` 格式（如 `D1@凸台-拉伸1`），特征名随语言本地化。
- **SolidWorks 关闭后**：首次 `sw_connect` 会重新启动它（较慢）。
