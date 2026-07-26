# 项目结构说明

本文档用于说明 `atk_nl_codegen_demo` 项目的目录结构、核心文件职责，以及当前 Demo 的运行流程。

## 目录总览

```text
atk_nl_codegen_demo/
├─ app.py
├─ web_app.py
├─ README.md
├─ PROJECT_STRUCTURE.md
├─ requirements.txt
├─ .gitignore
├─ examples/
│  ├─ sample_inputs.md
│  └─ sample_task.json
├─ generated/
│  ├─ README.md
│  ├─ structured_task.json
│  ├─ execution_plan.md
│  ├─ generated_connect_inclination_change.py
│  ├─ generated_connect_single_satellite_orbit.py
│  ├─ validation_report.md
│  ├─ connect_execution_log.json
│  └─ connect_execution_log.md
├─ schemas/
│  └─ inclination_change_transfer.schema.json
├─ src/
│  ├─ __init__.py
│  ├─ models.py
│  ├─ nlp_parser.py
│  ├─ validators.py
│  ├─ code_generator.py
│  ├─ help_links.py
│  ├─ verifier.py
│  └─ demo_runner.py
├─ templates/
│  ├─ connect_inclination_change.py.j2
│  └─ connect_single_satellite_orbit.py.j2
└─ web/
   ├─ index.html
   ├─ styles.css
   └─ app.js
```

## 根目录文件

### `app.py`

命令行入口文件。

负责：

- 接收用户输入的自然语言任务。
- 支持 `--example` 参数运行内置示例。
- 调用 `src/demo_runner.py` 中的主流程。

示例：

```powershell
python app.py --example
```

或：

```powershell
python app.py "创建一个倾角改变轨道机动规划场景，从2022年11月5日开始，初始轨道半长轴6570000米，倾角28度，远地点到42160000米，最后倾角降到0度"
```

### `web_app.py`

本地 Web 演示入口文件。

负责：

- 启动 `127.0.0.1:8765` 本地网页服务。
- 提供自然语言解析接口 `/api/parse`。
- 提供执行日志读取接口 `/api/logs`。
- 提供命令帮助定位接口 `/api/help`。
- 托管 `web/` 目录下的静态页面资源。

示例：

```powershell
python web_app.py
```

### `README.md`

项目总说明文件。

负责：

- 介绍 Demo 的目标。
- 说明当前支持的功能。
- 说明运行方式。
- 说明当前边界：规则解析版、少量任务模板、多轮追问仍是预留能力。

### `PROJECT_STRUCTURE.md`

当前文件。

负责：

- 记录项目结构。
- 说明每个目录和文件的用途。
- 方便之后继续开发、交接或给面试负责人解释项目。

### `requirements.txt`

依赖说明文件。

当前项目只使用 Python 标准库，所以没有第三方依赖。

### `.gitignore`

Git 忽略规则。

负责忽略：

- Python 缓存文件。
- 虚拟环境。
- PyCharm 本地配置。
- `generated/` 下反复生成的演示结果。

## `examples/`

示例输入和示例结构化任务目录。

### `examples/sample_inputs.md`

自然语言输入示例。

包含：

- 完整输入。
- 较口语化输入。
- 模糊输入。

用途：

- 演示时可以直接复制里面的句子运行。
- 后续扩展测试用例时，可以继续往这里追加更多自然语言表达。

### `examples/sample_task.json`

结构化任务 JSON 示例。

用途：

- 展示自然语言解析后应该得到什么样的数据结构。
- 给后续大模型 JSON Schema 输出提供参考。
- 也可以用于模板生成和校验逻辑的手工测试。

## `generated/`

生成结果目录。

运行 Demo 后，会在这里输出当前任务的结果文件。

注意：

- 除 `generated/README.md` 外，其他生成文件默认不提交到 Git。
- 这些文件可以反复覆盖生成。

### `generated/README.md`

说明生成结果目录的用途。

### `generated/structured_task.json`

自然语言解析后的结构化任务结果。

它体现的是：

```text
用户自然语言 → 受约束任务 JSON
```

里面包含：

- 任务类型。
- 场景名。
- 卫星名。
- 分析时间。
- 初始轨道参数。
- 目标约束。
- MCS 设置。
- 原始输入。
- 默认假设。

### `generated/execution_plan.md`

用户可读执行计划。

用途：

- 在真正生成或执行 ATK 命令前，让用户知道系统理解成了什么。
- 未来可以作为“执行前确认”的展示内容。

### `generated/generated_connect_inclination_change.py`

根据结构化任务和模板生成的 Connect Python 代码。

用途：

- 展示最终二次开发代码生成结果。
- 后续在 ATK 环境具备时，可以进一步尝试真实执行。
- 当前已验证可在外部 Python 环境中连接 ATK，并在 ATK 中显示三维模型效果。
- 脚本会记录全部 Connect 命令和返回内容；遇到 `NACK` 或 `FALSE` 会打印警告但不终止流程。
- 运行结束后会生成 `connect_execution_log.json` 和 `connect_execution_log.md`，方便之后做网页筛选展示。

注意：

- 运行前需要先启动 ATK，并确保 Connect 端口为 `6655`。
- 运行目录中需要有 `ATKConnectModule.py` 和 `_ATKConnectModule.pyd`。
- 多数设置类 Connect 命令可能返回空；如果命令写错，ATK 可能只返回 `NACK`，不会提供详细错误原因。

### `generated/generated_connect_single_satellite_orbit.py`

根据单卫星绕行任务模板生成的 Connect Python 代码。

用途：

- 展示非 Astrogator 复杂机动规划之外的第二类任务模板。
- 创建场景和卫星。
- 使用 `SetState Classical` 设置卫星经典轨道。
- 设置约一圈轨道的分析时间。
- 复用 Connect 执行日志机制。

### `generated/validation_report.md`

自主验证报告。

这是当前 Demo 的核心亮点之一。

负责说明：

- 识别到了什么任务。
- 使用了哪些默认假设。
- 参数校验是否通过。
- 生成代码是否包含关键 Connect 流程。
- 当前验证类型是 Dry Run / 代码级验证。

## `schemas/`

结构化任务 Schema 目录。

### `schemas/inclination_change_transfer.schema.json`

倾角改变转移任务的 JSON Schema 草案。

用途：

- 约束结构化任务字段。
- 给后续大模型 Structured Outputs / JSON Schema 输出提供基础。
- 说明当前任务必须包含哪些核心字段。

当前 Schema 还比较基础，后续可以继续增强：

- 参数类型。
- 单位枚举。
- 数值范围。
- 更严格的必填字段。
- 多任务模板支持。

## `src/`

核心业务代码目录。

### `src/__init__.py`

Python 包初始化文件。

作用：

- 标记 `src` 是一个 Python 包。
- 方便 `app.py` 导入 `src.demo_runner`。

### `src/models.py`

结构化任务数据模型。

负责定义：

- `Quantity`：带单位的数值。
- `TimePeriod`：分析时间范围。
- `InitialOrbit`：初始轨道参数。
- `TransferTargets`：目标约束。
- `McsSettings`：MCS 设置。
- `StructuredTask`：完整结构化任务。

它的作用是让任务数据保持清晰、稳定，避免在代码里到处传散乱字典。

### `src/nlp_parser.py`

自然语言解析模块。

当前使用的是规则解析，不是大模型解析。

负责：

- 识别当前任务是否像“倾角改变转移”。
- 从自然语言中提取日期。
- 提取半长轴、偏心率、倾角、远地点半径、最终倾角等参数。
- 识别不到的参数使用默认值，并记录到 `assumptions`。

当前规则解析的特点：

- 优点：稳定、无需 API、不会乱编命令。
- 缺点：泛化能力有限，只能处理预设表达方式。

后续如果接入大模型，主要替换这个模块即可。

### `src/validators.py`

任务校验和执行计划生成模块。

负责：

- 校验任务类型是否支持。
- 校验场景名、卫星名是否存在。
- 校验半长轴是否大于地球半径。
- 校验偏心率范围。
- 校验倾角范围。
- 校验目标远地点是否大于初始半长轴。
- 生成用户可读执行计划。

它体现的是：

```text
AI 负责理解，程序负责约束和校验
```

### `src/code_generator.py`

Connect 代码生成模块。

负责：

- 根据任务类型读取对应的 Connect 代码模板。
- 把结构化任务中的参数填入模板。
- 输出最终 Connect Python 代码。

当前实现使用简单字符串替换，暂未引入 Jinja2 依赖。

这样做的好处：

- 无第三方依赖。
- 演示稳定。
- 后续如果模板变复杂，可以再替换成 Jinja2。

### `src/verifier.py`

生成代码自主验证模块。

负责：

- 检查生成代码是否包含关键 Connect 命令。
- 检查关键参数是否已写入代码。
- 生成验证报告。

验证内容包括：

- 是否建立连接。
- 是否创建场景。
- 是否创建卫星。
- 是否设置分析时间。
- 是否启用 Astrogator。
- 是否插入 Propagate、Target Sequence、Maneuver。
- 是否设置初始轨道参数。
- 是否设置远地点、偏心率、倾角约束。
- 是否运行 MCS。
- 是否关闭连接。

这是 Demo 的可信亮点之一。

### `src/help_links.py`

Connect 命令帮助定位模块。

负责：

- 把执行日志中的命令名和参数映射到 ATK 本地帮助页。
- 为 `New`、`SetAnalysisTimePeriod`、`Animate`、`Graphics`、`Astrogator` 等命令提供语法、示例和排错提示。
- 供网页接口 `/api/help` 按需查询，用户不点击帮助按钮时不会额外搜索文档。

当前实现是轻量映射，不在运行时全文扫描 ATK 帮助目录。

### `src/demo_runner.py`

主流程编排模块。

负责把各模块串起来：

```text
自然语言输入
→ nlp_parser 解析
→ validators 校验
→ validators 生成执行计划
→ code_generator 生成 Connect 代码
→ verifier 自主验证
→ 写入 generated 目录
```

这是当前 Demo 的核心调度中心。

## `web/`

本地网页界面目录。

### `web/index.html`

网页结构文件。

负责展示：

- 自然语言输入区。
- 结构化任务 JSON。
- 完整可读执行计划。
- 预留追问区。
- 自主验证报告。
- 生成的 Connect Python 代码。
- Connect 执行日志和 NACK 帮助按钮。

### `web/styles.css`

网页样式文件。

负责：

- 页面布局。
- 卡片、代码块、日志行、状态标签和弹窗样式。
- OK 与 NACK 执行结果的颜色区分。

### `web/app.js`

网页交互脚本。

负责：

- 调用 `/api/sample` 填入示例。
- 调用 `/api/parse` 解析自然语言并刷新理解结果。
- 调用 `/api/logs` 读取 Connect 执行日志。
- 按全部、NACK、OK 筛选日志。
- 对 NACK 命令调用 `/api/help` 并弹出帮助说明。

## `templates/`

代码模板目录。

### `templates/connect_inclination_change.py.j2`

Connect Python 代码模板。

负责定义倾角改变转移任务的固定命令流程。

### `templates/connect_single_satellite_orbit.py.j2`

Connect Python 代码模板。

负责定义单卫星绕地显示任务的固定命令流程，核心命令包括 `New`、`SetAnalysisTimePeriod`、`SetState Classical`、`Graphics` 和 `Animate`。

模板中使用占位符，例如：

```text
{{scenario_name}}
{{satellite_name}}
{{start_time}}
{{sma}}
{{inc}}
{{apoapsis_radius}}
{{final_inclination}}
```

代码生成时，`src/code_generator.py` 会把这些占位符替换为结构化任务中的真实参数。

## 当前 Demo 流程

运行：

```powershell
python app.py --example
```

实际流程：

```text
app.py
→ src/demo_runner.py
→ src/nlp_parser.py
→ src/validators.py
→ src/code_generator.py
→ src/verifier.py
→ generated/
```

输出文件：

```text
generated/structured_task.json
generated/execution_plan.md
generated/generated_connect_inclination_change.py
generated/generated_connect_single_satellite_orbit.py
generated/validation_report.md
generated/connect_execution_log.json
generated/connect_execution_log.md
```

也可以启动网页：

```powershell
python web_app.py
```

网页流程：

```text
web/index.html
→ web/app.js
→ web_app.py
→ src/demo_runner.py
→ generated/
→ web_app.py 读取日志和帮助映射
→ 页面展示解析结果、生成代码、执行日志和 NACK 帮助
```

## 当前完成度

当前项目已经完成：

- 两个任务模板闭环：倾角改变转移、单卫星绕行。
- 规则版自然语言解析。
- 简单意图分类和不支持任务拒绝。
- 结构化任务生成。
- 参数校验。
- Connect Python 代码生成。
- 自主验证报告。
- Dry Run 演示。
- 外部 Python 直接连接 ATK 执行。
- ATK 三维模型效果验证。
- Connect 命令不中断式运行日志与 `NACK` 警告记录。
- 本地 Web 页面演示。
- NACK 命令帮助页按需定位。

当前尚未完成：

- 大模型解析。
- 更丰富的任务模板。
- 多轮缺参追问。
- Web 端一键启动 ATK 或直接执行生成脚本。
- Component 后端。

## 后续扩展建议

建议按以下顺序扩展：

1. 增强 `schemas/inclination_change_transfer.schema.json` 的字段约束。
2. 把 `src/nlp_parser.py` 替换或扩展为大模型 JSON Schema 解析。
3. 加入真正的缺参追问机制。
4. 增加更多任务模板，例如霍曼转移、场景创建、卫星轨道设置、可见性分析。
5. 在 Web 端增加“运行生成脚本”按钮，调用真实 ATK Connect 执行器。
6. 增加 Component 后端，把同一个结构化任务映射到 Component Python。
7. 把 NACK 帮助映射扩展成更完整的命令知识库。
