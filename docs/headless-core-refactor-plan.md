# Headless Core Refactor Status

目标：移除旧 CustomTkinter UI，把 WPF 作为唯一用户界面，Python 只保留可打包、可测试、可由 WPF 启停的 headless 自动化核心。

## 当前状态

- `main.py` 已变为极薄兼容入口，只处理 `--headless` 旧参数并委托到 `fh6auto_core.headless.main(...)`。
- 旧 CustomTkinter UI、迷你面板、F3 测试入口、旧 Python 热键监听和 `main ocr test.py` 已从源码树删除。
- `fh6auto_core.headless` 直接创建 `HeadlessAutomationBot`，不会导入旧 `main.py` UI 类。
- `headless_shims.py`、`legacy_runtime.py`、`legacy_tasks.py`、`legacy_pipeline.py`、`legacy_hotkeys.py`、`legacy_test_tools.py` 已删除。
- `RaceTask`、`BuyCarTask`、`WheelspinTask`、`SellCarTask` 通过 `AutomationContext` 访问运行状态、输入、视觉和恢复服务，不再读取旧 UI 控件。
- WPF 负责配置、日志、启动/停止、全局开始/停止热键、悬浮窗、技能路径、流程计算和发布包中的 core 启动。
- Python core 负责图像识别、输入控制、窗口/恢复逻辑、pipeline 调度和任务执行。

## 保留功能清单

- 启动/停止：WPF `FH6CoreBridge` 启动 `FH6AutoCore.exe`，缺失时回退到 `python -m fh6auto_core.headless`。
- 日志：WPF 读取 core 标准输出/错误输出并显示。
- 热键：WPF 注册开始/停止全局热键，默认开始 `F7`、停止 `F8`。
- 配置：WPF 与 Python 共享 `config.json` 字段和默认值。
- 计算器：WPF `FH6PipelineCalculator` 与 Python `pipeline_calculator` 保持同一规则。
- 技能路径：WPF `FH6SkillPath` 与 Python `skill_path` 保持同一规则。
- 更新检查：Python `support.check_for_update` 保留为可复用函数；当前 WPF 页面尚未暴露独立更新检查按钮。
- 测试工具：旧 F3/启动测试 UI 已删除；后续若需要，应作为独立 headless diagnostics 命令重新设计。

## 验收标准

- `python -m fh6auto_core.headless --help` 正常。
- `python main.py --headless --help` 正常。
- 单元测试通过。
- `dotnet build .\ui\FH6Auto.UI.sln -c Debug` 通过。
- `.\scripts\verify.ps1 -Release` 能生成并探测包含 `FH6Farm.exe`、`FH6AutoCore.exe`、`config.json` 的发布包。
