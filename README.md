# 📱 手机自动化智能代理

面向Android设备的自然语言自动化执行平台，结合大模型感知、设备控制与隐私保护，实现“说一句话，自动完成手机操作”。项目提供命令行、图形界面及批量执行三种使用方式，并支持结果回放与日志追踪。

## 功能亮点

- **自然语言驱动**：通过 `TaskExecutor` 调用大模型（Doubao / Qwen 系列），解析界面 XML + 截图并规划下一步操作。
- **多终端入口**：支持命令行交互、Tkinter 图形界面以及读取 Excel 的批量任务执行。
- **自动化设备管理**：`DeviceController` 基于 `uiautomator2`/`adbutils` 自动发现并连接手机，执行点击、滑动、文本输入等操作。
- **隐私防护**：`PrivacyProtector` 对手机号、姓名、地址等敏感信息进行检测与截图假名化处理。
- **完整留痕**：每一步生成原始截图、标注图、XML 以及动作决策 JSON，便于复盘与回放。

## 系统架构概览

```
Android 手机  ←→  uiautomator2 / adb  ←→  DeviceController
                                     │
                                     ├─ TaskExecutor —— 协调执行主循环
                                     │      ├─ AIAnalyzer（Ark OpenAI SDK）
                                     │      ├─ PrivacyProtector
                                     │      ├─ ImageMarker / 输出管理
                                     │      └─ KnowledgeBase（行业规则提示）
                                     │
入口层：main.py（CLI）│ gui_app_new.py（GUI）│ batch_executor.py（批量）
```

核心目录速览：

| 模块/脚本 | 作用 |
| --- | --- |
| `src/task_executor.py` | 执行主循环：采集界面 → 调用大模型 → 执行动作 → 保存结果 |
| `src/ai_analyzer.py` | 调用 Doubao/Ark OpenAI 接口，解析模型输出并做字段校验 |
| `src/device_controller.py` | 连接设备、执行触控/滑动/输入、抓取截图与 XML |
| `src/privacy_protector.py` | 根据模型返回的敏感区域对截图做假名化处理 |
| `app/main_window.py` 等 | Tkinter GUI，包含设备/任务/配置管理面板 |
| `batch_executor.py` | 按 Excel `示例query` 列批量运行任务并产出报告 |
| `utils/image_marker.py` | 在截图上标记点击区域，生成 `_label` 图片 |

## 安装与环境准备

1. **系统要求**
   - Windows 10 或以上（推荐），macOS/Linux 亦可运行命令行模式
   - Python 3.10+
   - 已安装 adb，并可在命令行直接执行

2. **克隆代码并安装依赖**
   ```bash
   git clone <repo-url>
   cd Android-auto-rongyao
   python -m venv .venv && .venv\Scripts\activate     # Windows 示例
   pip install -r requirements.txt
   python -m uiautomator2 init                        # 初始化设备驱动
   ```

3. **配置环境变量**
   - `DASHSCOPE_API_KEY`：阿里云 DashScope 密钥（用于兼容旧流程，缺失会报警）
   - `ARK_API_KEY`：火山方舟 OpenAI API 密钥，默认模型为 `doubao-1-5-thinking-vision-pro-250428`
   在 PowerShell 示例：
   ```powershell
   setx DASHSCOPE_API_KEY "your_dashscope_key"
   setx ARK_API_KEY "your_ark_key"
   ```

4. **准备设备**
   - 手机开启开发者模式与 USB 调试
   - 连接电脑并授权调试；`adb devices` 能显示设备
   - 保持屏幕点亮，避免锁屏打断流程

## 启动方式

- **命令行模式**
  ```bash
  python main.py
  ```
  交互式输入任务描述，可多轮执行；输出保存在 `output/<任务>`。

- **图形界面**
  ```bash
  python gui_app_new.py
  ```
  启动 Tkinter GUI，提供设备检测、单任务、批量任务、配置管理、隐私开关、日志面板等功能。

- **批量执行**
  ```bash
  python batch_executor.py
  ```
  读取 `验收通过数据/标贝采集需求.xlsx` 中各 Sheet 的 `示例query` 列，逐条执行并生成统计报告。可在启动时选择全部/部分 Sheet 或单个测试任务，结果保存到 `batch_output_*` 与指定的单任务输出目录。

- **打包版本（可选）**
  - `build_with_pyinstaller.bat`：使用 PyInstaller 打包 GUI。
  - `dist/phone-agent工具.exe`：历史打包产物，可直接双击体验（需同目录配置文件和依赖环境）。

## 运行产物与日志

- `output/<任务名>/`：单次执行所有产物（截图、标注图、XML、任务 JSON、隐私处理后的截图等）。
- `batch_output_*/`：批量执行的任务归档与 `*_execution_results.json` 明细。
- `logs/phone_auto_*.log`：按日期滚动的运行日志。
- `gui_config.json`：GUI 配置、输出目录与包名映射等持久化信息。

## 模块与目录说明

```
.
├─ main.py / gui_app_new.py / batch_executor.py      # 三类入口
├─ src/
│  ├─ ai_analyzer.py            # 调用大模型，解析并格式化结果
│  ├─ device_controller.py      # 设备链接、动作执行、截图/抓取 XML
│  ├─ task_executor.py          # 执行主循环与中断/人工介入/成果保存
│  ├─ action_parser.py          # 通用动作解析与坐标处理工具
│  ├─ config.py                 # 全局配置，含模型参数、隐私设定、包名
│  ├─ knowledge_base.py         # 基于意图的行业规则补充
│  ├─ privacy_protector.py      # 敏感信息检测与假名化
│  ├─ prompt_engineering/       # 提示词与领域策略模版
│  └─ logger_config.py          # Loguru 封装
├─ app/                         # Tkinter GUI
│  ├─ main_window.py            # GUI 应用入口
│  ├─ managers/                 # 设备/任务/配置管理器
│  ├─ components/               # 复用 UI 组件
│  └─ dialogs/                  # 人工介入、配置等对话框
├─ utils/
│  ├─ image_marker.py           # 操作标注图生成
│  ├─ phone_number_processor.py # 图像级手机号假名化
│  └─ text_processor.py         # 通用文本区域处理
├─ visualize_ui.py              # UI 层级可视化辅助工具
└─ requirements.txt             # 依赖清单
```

## 调参与扩展要点

- **模型切换**：在 `src/config.py` 修改 `model_name` 以及 `model_params`；支持设置温度、最大 tokens、JSON 输出格式等。
- **应用包名映射**：可在 GUI 中动态管理，也可直接编辑 `config.app_packages`。
- **最大执行步数**：默认 50，可视任务复杂度调整 `config.max_execution_times`。
- **人工介入流程**：当任务需要人工决策时，GUI 会触发人工介入对话框，`TaskExecutor` 支持从指定步骤重新执行。
- **隐私策略**：`config.privacy_protection` 可单独关闭手机号、地址、姓名的假名化功能，或开启调试模式观察处理细节。

## 常见问题排查

- **设备无法连接**
  - `adb devices` 检查设备状态，必要时执行 `adb kill-server & adb start-server`
  - 确认 USB 调试与文件传输权限已授予
  - 多设备场景下，命令行会提示选择序号

- **模型调用失败**
  - 确保已正确设置 `DASHSCOPE_API_KEY` 与 `ARK_API_KEY`
  - 检查网络是否可访问火山方舟/阿里云接口
  - 查看 `logs/phone_auto_*.log` 获取详细报错

- **任务长时间无响应**
  - 手机屏幕是否被锁定或弹窗遮挡
  - 通过 GUI 或命令行触发“中断任务”，重新执行
  - 适当提高 `config.max_execution_times` 或在 GUI 中开启人工审核模式

- **隐私截图未变更**
  - 模型需返回 `privacy_detection` 字段才会触发假名化
  - 检查 `config.privacy_protection.enabled` 是否开启

## 许可

本项目基于 MIT License 发布，详情见 `LICENSE`。

---

如需进一步迁移或功能扩展，建议从 `TaskExecutor` 的执行流程与 `AIAnalyzer` 的模型接口入手；遇到疑问可参考 `logs/` 中的详细日志记录。祝交接顺利。
