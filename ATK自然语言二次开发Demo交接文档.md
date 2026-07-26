# ATK 自然语言二次开发 Demo 交接文档

生成时间：2026-07-25  
当前目标：在下周三前完成一个可演示的 ATK 自然语言二次开发 Demo，用于向项目负责人展示“用户通过自然语言使用 ATK”的可行性、可信度和特色亮点。

---

## 1. 背景概述

前天面试时，项目负责人询问了“如何让用户通过自然语言使用 ATK 软件”的问题，并提到了 ATK 的二次开发部件。

面试后，已进一步查看 ATK 本地帮助文档与二次开发案例，形成了一个初步技术设想：

> 不让大模型直接自由生成或执行 ATK 命令，而是设计一个自然语言任务编排系统。AI 负责理解用户意图、抽取参数和规划任务；程序负责 Schema 约束、参数校验、模板生成、执行验证与结果反馈。

负责人反馈：

> 理解挺好的，你能把你说的做一个 demo 吗？选择 ATK 的一个功能，按照你思考的初步自己实现一个二次开发代码生成与自主验证的例子。主要看达成效果：第一是否可行可信，第二是否有特色亮点。

因此当前任务不是做完整产品，而是做一个**单功能闭环 Demo**。

---

## 2. 当前推荐 Demo 路线

推荐优先做：

> **基于 Connect Python 案例的自然语言到二次开发代码生成与自主验证 Demo。**

原因：

1. Connect Python 案例已经是线性命令序列，适合做成模板。
2. 短期内更容易实现自然语言 → 结构化任务 → Connect 代码生成 → 验证报告。
3. 相比 Component，Connect 环境依赖更少，更适合快速演示“外部 AI 助手控制 ATK”的可行性。
4. 亮点不在于 Connect 本身，而在于**可信生成流程**：
   - 先生成结构化任务；
   - 再校验参数；
   - 再通过固定模板生成代码；
   - 最后输出自主验证报告。

Component 不是不合适，而是更适合作为后续深度集成路线：

> Connect 适合第一阶段 MVP；Component 适合复杂任务模板、对象级封装和长期产品化扩展。

---

## 3. 已查看的 ATK 文档与案例

### 3.1 ATK 帮助文档目录

完整帮助文档目录：

```text
D:\Shana\ATK-4.0.1\Help\html
```

二次开发教程目录：

```text
D:\Shana\ATK-4.0.1\Help\html\二次开发教程
```

已查看重点：

```text
D:\Shana\ATK-4.0.1\Help\html\二次开发教程\1-二次开发说明.html
D:\Shana\ATK-4.0.1\Help\html\二次开发教程\2-二次开发CONNECT模式\index.html
D:\Shana\ATK-4.0.1\Help\html\二次开发教程\3-MBSE接口\index.html
D:\Shana\ATK-4.0.1\Help\html\二次开发教程\4-二次开发COMPONENT模式\index.html
```

完整帮助目录大致扫描结果：

```text
总 HTML 页面数：约 921

01-安装：17
02-案例教程：40
03-基础使用指南：116
04-理论基础：7
5.专业使用指南：165
topics：70
二次开发教程：491
发布说明：4
综合案例：9
```

### 3.2 Connect Python 案例

用户提供的 Connect Python 完整案例路径：

```text
C:\Users\shana\.codex\attachments\79076c66-f3dc-4c10-81b1-8f71f45d634e\pasted-text.txt
```

该案例主要流程：

1. 建立连接：

```python
conID = atkOpen('127.0.0.1', 6655)
```

2. 新建场景和卫星：

```python
atkConnect(conID, 'New', '/ Scenario InclinationChange')
atkConnect(conID, 'New', '/ Satellite SatInclinationChange')
```

3. 设置分析时间：

```python
atkConnect(conID, 'SetAnalysisTimePeriod', '* "5 Nov 2022 00:00:00.000" "8 Nov 2022 00:00:00.000"')
```

4. 设置卫星轨道预报器为 Astrogator / 机动规划：

```python
atkConnect(conID, 'Astrogator', '*/Satellite/SatInclinationChange SetProp')
```

5. 构建机动规划序列：
   - `Propagate`
   - `Target_Sequence`
   - `Maneuver`
   - `Propagate1`
   - `Target_Sequence1`
   - `Maneuver`
   - `Propagate2`
   - `Target_Sequence2`
   - `Maneuver`
   - `Propagate3`

6. 设置初始轨道参数：
   - Epoch：`5 Nov 2022 00:00:00.000 UTCG`
   - CoordinateType：`Modified Keplerian`
   - sma：`6570000 m`
   - ecc：`0`
   - inc：`28 deg`
   - RAAN：`0`
   - w：`0`
   - ta：`0`

7. 第一组瞄准序列：
   - 目标：抬升远地点半径到 `42160000 m`
   - 控制变量：`ImpulsiveMnvr.Cartesian.X`
   - 约束：`Radius Of Apoapsis`

8. 第二组瞄准序列：
   - 目标：在远地点圆化轨道
   - 约束：`Eccentricity = 0`

9. 第三组瞄准序列：
   - 目标：在升交点改变倾角
   - 控制变量：`ImpulsiveMnvr.Cartesian.X`、`ImpulsiveMnvr.Cartesian.Y`
   - 约束：`Inclination = 0 deg`、`Eccentricity = 0`

10. 最终预报段：
    - 停止条件：`Duration`
    - 时长：`129600 sec`

11. 运行 MCS：

```python
atkConnect(conID, 'Astrogator', '*/Satellite/SatInclinationChange RunMCS')
```

12. 关闭连接：

```python
atkClose(conID)
```

### 3.3 Component Python 案例

Component Python 操作流程目录：

```text
D:\Shana\ATK-4.0.1\Help\html\二次开发教程\4-二次开发COMPONENT模式\4-Python操作流程
```

其中包含：

```text
1-案例介绍.html
2-案例实现.html
3-案例结果.html
index.html
```

案例依赖：

```text
IntegratingWithATK/python-3.8.0-embed-amd64
ATKComponentPythonModule.py
_ATKComponentPythonModule.pyd
ATKComponentJava.dll
ATKComponentPythonTest.py
```

Component Python 案例说明：

1. 可以通过 `ATKComponentPythonModule` 调用 Component 模式接口。
2. 可以新建场景、创建卫星、设置轨道、配置 Astrogator/MCS、运行仿真、输出报告、保存想定文件。
3. 典型对象调用方式包括：

```python
pIAtkObjectRoot = ATKModule.IAtkObjectRoot()
pIScenario = pIAtkObjectRoot.GetChildren().New(ATKModule.eScenario, "FastTransfer")
pISatellite = pIScenario.GetChildren().New(ATKModule.eSatellite, "Satellite1")
pISatellite.SetPropagatorType(ATKModule.ePropagatorAstromaster)
pIVADriverMCS = pISatellite.GetPropagator()
pIVAMCSSegmentCollection = pIVADriverMCS.GetMainSequence()
```

判断：

> Component 并非不合适。它更像对象化 SDK/组件层，适合长期封装复杂专业能力。但短期 Demo 更推荐 Connect，因为 Connect 更轻、更线性、更容易做出可演示闭环。

---

## 4. Connect 与 Component 的理解

### 4.1 Connect 模式

Connect 更像 ATK 暴露出来的远程命令控制层。

特点：

1. 通过端口连接 ATK。
2. 默认端口通常为 `6655`。
3. 通过 `atkOpen`、`atkConnect`、`atkClose` 与 ATK 交互。
4. 实际功能由 Connect 命令库提供。
5. 命令是严格文本格式，路径、参数、单位、引号、空格都比较敏感。

优点：

1. 外部程序容易接入。
2. 适合快速验证自然语言控制 ATK。
3. 适合做代码生成模板。
4. 比 Component 更适合短期 Demo。

缺点：

1. 文本命令容易写错。
2. 复杂流程中的对象路径较长。
3. 不适合让 AI 完全自由生成。

### 4.2 Component 模式

Component 更像对象化 SDK/组件接口。

特点：

1. 通过动态库和语言接口调用 ATK 能力。
2. Python 下依赖 `ATKComponentPythonModule.py` 和 `_ATKComponentPythonModule.pyd`。
3. 以对象、类、枚举、方法的方式操作 ATK。
4. 可以新建场景、卫星、传感器、覆盖定义、链、高级接近分析、Astrogator/MCS 等对象。

优点：

1. 结构化程度更高。
2. 适合封装复杂业务能力。
3. 长期工程化可能比 Connect 更稳。
4. 更适合做专业任务函数库。

缺点：

1. 环境依赖更复杂。
2. 对对象模型理解要求更高。
3. 短期 Demo 容易卡在运行环境、动态库、接口细节上。

### 4.3 二者关系

可以在概念上这样理解：

> Connect 是面向脚本和远程控制的文本命令接口；Component 是面向软件集成的对象化接口。

但不能严格断言：

> Connect 就一定是 Component 的直接封装。

更准确的说法：

> 二者都是 ATK 的二次开发能力入口，面向不同集成场景。Connect 更适合轻量控制，Component 更适合深度集成。

---

## 5. 核心技术路线

不要让 AI 直接把自然语言翻译成 Connect 命令。

推荐流程：

```text
用户自然语言
→ AI 理解用户意图
→ 选择已有任务模板
→ 抽取关键参数
→ 生成结构化任务 JSON
→ Schema 校验
→ 领域规则校验
→ 缺参追问或歧义确认
→ 生成用户可读执行计划
→ 用户确认
→ 套用固定 Connect/Component 模板
→ 生成二次开发代码
→ 自主验证代码
→ 可选调用 ATK 执行
→ 输出结果与验证报告
```

核心分工：

```text
AI：理解、拆解、规划、抽取参数
程序：约束、校验、模板生成、执行、验证、日志
ATK：执行航天任务仿真与分析
```

一句话总结：

> AI 是任务规划员，模板是施工图，ATK 是执行设备。

---

## 6. 为什么不让 AI 直接生成 Connect 命令

主要原因：

1. Connect 命令格式严格，路径、参数、单位、引号、空格、顺序都容易出错。
2. 大模型可能产生幻觉，生成看似合理但文档中不存在的命令或参数。
3. 复杂 Astrogator/MCS 流程依赖顺序，错误一步后续都可能失败。
4. 自然语言常常存在歧义，例如“转到 GEO”可能对应霍曼转移、快速转移、倾角改变转移等不同流程。
5. 一些命令可能创建、覆盖、删除或长时间计算，需要用户确认和权限控制。
6. 直接自由生成命令难测试、难维护、难复用。

因此应改为：

```text
自然语言 → 结构化任务 → 模板生成命令
```

而不是：

```text
自然语言 → AI 自由生成命令
```

---

## 7. Demo 目标定义

### 7.1 Demo 名称

可以命名为：

```text
ATK Natural Language CodeGen Demo
ATK 自然语言二次开发代码生成与验证 Demo
ATK Copilot Demo
```

### 7.2 Demo 最小目标

做一个单功能闭环：

> 用户输入一句自然语言，系统识别任务类型和参数，生成结构化 JSON，校验参数，生成 Connect Python 二次开发代码，并输出自主验证报告。

### 7.3 推荐选题

首选：

```text
倾角改变转移任务：InclinationChange
```

原因：

1. 用户已有完整 Connect Python 案例。
2. 案例流程复杂度足够，能体现专业性。
3. 包含场景创建、卫星创建、轨道参数、Astrogator、Target Sequence、MCS 等关键步骤。
4. 适合展示“AI 不是直接写命令，而是生成结构化任务并通过模板可靠生成代码”。

备选：

```text
霍曼转移任务：HohmannTransfer
```

优点：

1. 概念更经典，解释更容易。
2. 参数更少，Demo 风险较低。

如果时间紧，建议先做霍曼转移；如果希望显得更专业，做倾角改变转移。

当前更推荐：

> 用倾角改变转移作为主 Demo，因为已有 Connect 案例完整，而且更能体现流程编排能力。

---

## 8. Demo 输入输出设计

### 8.1 示例用户输入

```text
创建一个倾角改变轨道机动规划场景，从 2022 年 11 月 5 日开始，初始轨道半长轴 6570000 米，偏心率 0，倾角 28 度，先抬升远地点到 42160000 米，再在远地点圆化轨道，最后在升交点把倾角降到 0 度，并运行 MCS。
```

也可以支持更口语化输入：

```text
帮我建一个从低轨转到 GEO 并把倾角从 28 度降到 0 度的任务，开始时间是 2022 年 11 月 5 日。
```

### 8.2 结构化任务 JSON 示例

```json
{
  "intent": "inclination_change_transfer",
  "scenario_name": "InclinationChange",
  "satellite_name": "SatInclinationChange",
  "time_period": {
    "start": "5 Nov 2022 00:00:00.000",
    "end": "8 Nov 2022 00:00:00.000"
  },
  "initial_orbit": {
    "coordinate_type": "Modified Keplerian",
    "epoch": "5 Nov 2022 00:00:00.000 UTCG",
    "sma": {
      "value": 6570000,
      "unit": "m"
    },
    "ecc": 0,
    "inc": {
      "value": 28,
      "unit": "deg"
    },
    "raan": {
      "value": 0,
      "unit": "deg"
    },
    "arg_perigee": {
      "value": 0,
      "unit": "deg"
    },
    "true_anomaly": {
      "value": 0,
      "unit": "deg"
    }
  },
  "targets": {
    "apoapsis_radius": {
      "value": 42160000,
      "unit": "m"
    },
    "final_eccentricity": 0,
    "final_inclination": {
      "value": 0,
      "unit": "deg"
    }
  },
  "mcs": {
    "run_after_generation": true,
    "final_propagate_duration": {
      "value": 129600,
      "unit": "sec"
    }
  }
}
```

### 8.3 可读执行计划示例

```text
系统理解到你要执行一个“倾角改变轨道机动规划”任务：

1. 连接本机 ATK，端口 6655。
2. 创建场景 InclinationChange。
3. 创建卫星 SatInclinationChange。
4. 设置分析时间为 2022-11-05 到 2022-11-08。
5. 设置卫星轨道预报器为 Astrogator。
6. 设置初始轨道：sma=6570000m，ecc=0，inc=28deg。
7. 添加第一组 Target Sequence，将远地点半径约束为 42160000m。
8. 添加第二组 Target Sequence，将偏心率约束为 0。
9. 添加第三组 Target Sequence，将倾角约束为 0deg，并保持偏心率为 0。
10. 添加最终预报段，飞行时长 129600sec。
11. 运行 MCS。
```

### 8.4 生成代码输出

生成一个 Python 文件，例如：

```text
generated_connect_inclination_change.py
```

文件内容应包含：

1. `atkOpen('127.0.0.1', 6655)`
2. `New Scenario`
3. `New Satellite`
4. `SetAnalysisTimePeriod`
5. `Astrogator SetProp`
6. `InsertSegment`
7. 初始轨道参数设置
8. Target Sequence 配置
9. 控制变量设置
10. 约束设置
11. `RunMCS`
12. `atkClose(conID)`

### 8.5 自主验证报告示例

```text
ATK 二次开发代码自主验证报告

✅ 任务类型：inclination_change_transfer
✅ 已生成 Connect Python 代码
✅ 已包含 ATK 连接步骤
✅ 已包含场景创建步骤
✅ 已包含卫星创建步骤
✅ 已包含分析时间设置
✅ 已包含 Astrogator 机动规划启用步骤
✅ 已包含初始轨道六根数设置
✅ 已包含远地点半径目标约束
✅ 已包含偏心率目标约束
✅ 已包含倾角目标约束
✅ 已包含 MCS 运行命令
✅ 已包含关闭连接命令

参数校验：
✅ sma = 6570000 m，数值大于地球半径，合理
✅ ecc = 0，位于 [0, 1) 范围内
✅ inc = 28 deg，位于 [0, 180] 范围内
✅ target inclination = 0 deg，位于 [0, 180] 范围内
✅ apoapsis radius = 42160000 m，大于初始半长轴

风险提示：
⚠️ 当前仅完成代码级验证，是否能运行成功取决于 ATK 是否启动、端口是否开启、Connect 命令库是否与当前版本一致。
```

---

## 9. 自主验证设计

自主验证是本 Demo 的重点亮点。

不要只展示“生成代码”，而要展示：

> 生成前知道自己要做什么，生成后知道自己生成的东西是否满足任务约束。

### 9.1 验证层级

建议做三层验证：

#### 第一层：结构化任务验证

检查：

1. `intent` 是否在任务白名单中。
2. 必填字段是否存在。
3. 时间字段是否可解析。
4. 数值字段是否为数字。
5. 单位是否受支持。
6. 轨道参数是否在合理范围。

#### 第二层：模板完整性验证

检查生成代码是否包含关键步骤：

1. 建立连接。
2. 创建场景。
3. 创建卫星。
4. 设置分析时间。
5. 设置 Astrogator。
6. 设置初始轨道。
7. 插入必要的 MCS 段。
8. 添加控制变量。
9. 添加目标约束。
10. 运行 MCS。
11. 关闭连接。

#### 第三层：可选运行验证

如果 ATK 已启动并打开 Connect 端口，则可以尝试执行生成代码，并验证：

1. 是否连接成功。
2. 每条命令是否返回成功。
3. 是否生成场景或输出文件。
4. 是否能在 ATK 视图窗口查看效果。

如果暂时不执行 ATK，也可以做“干运行”：

```text
Dry Run：仅验证结构化任务和代码模板，不真实调用 ATK。
```

### 9.2 缺参追问机制

如果用户输入：

```text
帮我做一个低轨到 GEO 的转移。
```

系统不应直接猜测所有参数，而应输出：

```json
{
  "intent": "orbit_transfer",
  "status": "need_clarification",
  "missing_fields": [
    "start_time",
    "initial_orbit_radius_or_sma",
    "initial_inclination",
    "transfer_type",
    "satellite_name"
  ]
}
```

并追问：

```text
请补充以下信息：
1. 使用霍曼转移、快速转移，还是倾角改变转移？
2. 初始轨道半长轴或半径是多少？
3. 初始倾角是多少？
4. 开始时间是什么？
```

---

## 10. 代码结构建议

建议 Demo 项目结构：

```text
atk_nl_codegen_demo/
  app.py
  README.md
  requirements.txt
  schemas/
    inclination_change_transfer.schema.json
  templates/
    connect_inclination_change.py.j2
  examples/
    sample_inputs.md
    sample_task.json
  generated/
    generated_connect_inclination_change.py
    validation_report.md
  src/
    nlp_parser.py
    task_schema.py
    validators.py
    code_generator.py
    verifier.py
    demo_runner.py
```

为了短期完成，也可以简化为：

```text
atk_nl_codegen_demo/
  app.py
  templates/
    connect_inclination_change.py.j2
  generated/
  README.md
```

### 10.1 模块职责

```text
nlp_parser.py
自然语言解析。负责调用 AI 或规则，把用户输入转换成结构化任务。

task_schema.py
定义任务字段、默认值、枚举值和必填项。

validators.py
校验任务参数，包括单位、范围、缺参、歧义和风险。

code_generator.py
根据结构化任务填充 Connect 代码模板。

verifier.py
验证生成代码是否包含必要命令和流程。

demo_runner.py
负责串联输入、解析、校验、生成、验证和输出。

app.py
演示入口，可以是命令行，也可以是简单网页界面。
```

---

## 11. 是否需要真实调用 OpenAI API

如果当前额度不足，可以先做两种模式：

### 11.1 规则模拟模式

适合快速演示：

1. 针对固定示例输入，用规则或少量关键词识别任务。
2. 抽取明显参数。
3. 生成结构化 JSON。
4. 生成代码和验证报告。

优点：

1. 不消耗 API 额度。
2. 稳定可控。
3. 适合下周三前交付。

缺点：

1. 自然语言泛化能力弱。
2. 更像原型，不像完整 AI 应用。

### 11.2 API 模式

如果有 API Key，可加入：

```text
自然语言 → OpenAI 模型 → JSON Schema 输出
```

重点：

1. 使用 JSON Schema / Structured Outputs 约束输出。
2. 不允许模型直接输出 Connect 命令。
3. 模型只输出结构化任务。
4. 程序仍然负责模板生成与验证。

建议：

> 下周三 Demo 可以先做规则模拟模式 + 预留 API 接口。这样即使额度不足，也能展示完整思路。

---

## 12. 特色亮点设计

负责人明确说“我这里已经有这个功能，看你短期内能做成什么样，有没有我这里还没考虑过的亮点”。

因此 Demo 不能只做“自然语言生成代码”，那样太普通。

建议强调以下亮点：

### 12.1 可信生成链路

展示：

```text
自然语言
→ 结构化任务
→ 参数校验
→ 执行计划
→ 模板代码
→ 自主验证报告
```

表达重点：

> 我没有让 AI 直接生成命令，而是把大模型限制在理解和规划层，真正执行的代码由受控模板生成。

### 12.2 自主验证报告

这可能是最重要的亮点。

展示系统不仅能生成代码，还能说明：

1. 识别了什么任务。
2. 抽取了哪些参数。
3. 哪些参数通过校验。
4. 生成代码包含哪些关键步骤。
5. 哪些部分需要用户确认。
6. 当前是干运行还是已连接 ATK 执行。

### 12.3 缺参追问

展示一个模糊输入：

```text
帮我建一个转移到 GEO 的任务。
```

系统不要乱生成，而是追问：

```text
你希望使用霍曼转移、快速转移，还是倾角改变转移？
请补充初始轨道半长轴、倾角、开始时间。
```

这能体现“可靠性”。

### 12.4 可解释执行计划

在生成代码前展示：

```text
我将执行以下步骤……
```

这让不懂 Connect 的用户也能理解系统要做什么。

### 12.5 后端可切换

设计上保留：

```text
backend = "connect"
backend = "component"
```

对外说明：

> 第一版用 Connect 生成代码，后续可把同一份结构化任务映射到 Component 后端。

这个点可以呼应已看过 Component 文档。

---

## 13. 下周三前开发计划

假设还有 4-5 天，建议按如下推进。

### 第一天：确定任务和模板

目标：

1. 确定只做 `inclination_change_transfer` 一个任务。
2. 整理 Connect 案例为参数化模板。
3. 定义结构化任务 JSON。
4. 明确必填字段和默认值。

输出：

```text
schema.json
connect_inclination_change.py.j2
sample_task.json
```

### 第二天：实现代码生成

目标：

1. 输入结构化 JSON。
2. 校验参数。
3. 填充模板。
4. 生成 Python Connect 代码。

输出：

```text
generated_connect_inclination_change.py
```

### 第三天：实现自然语言解析和缺参追问

目标：

1. 支持固定示例自然语言输入。
2. 抽取时间、半长轴、倾角、远地点目标、最终倾角等参数。
3. 缺参数时输出追问。

输出：

```text
自然语言 → JSON → 代码
```

### 第四天：实现自主验证报告

目标：

1. 验证结构化任务字段。
2. 验证代码关键命令。
3. 输出 Markdown 验证报告。
4. 支持 Dry Run。

输出：

```text
validation_report.md
```

### 第五天：整理演示和说明

目标：

1. 做一个简单命令行或网页界面。
2. 准备 2-3 个示例输入。
3. 准备 README。
4. 如果能跑 ATK，录屏展示实际效果。
5. 如果不能稳定跑 ATK，展示生成代码和验证报告。

---

## 14. 对负责人可汇报的话术

可以这样说：

```text
我准备先用 Connect 做一个闭环 Demo，因为 Connect 更适合快速验证自然语言到 ATK 二次开发代码生成的可行性。这个 Demo 的重点不是让大模型直接生成命令，而是先把自然语言转换成受约束的结构化任务，再通过模板生成 Connect Python 代码，并自动生成验证报告。

我会选择一个具体轨道机动规划功能，例如倾角改变转移。系统会展示：用户自然语言输入、AI/解析层识别出的任务 JSON、参数校验结果、生成的二次开发代码，以及自主验证报告。

Component 模式我也看了，它更适合作为后续复杂任务的深度执行后端。第一版先用 Connect 做出可信闭环，后续可以把同一个结构化任务映射到 Component。
```

如果被问难度：

```text
如果只做一个单功能闭环 Demo，难度可控，主要工作量在任务 Schema、模板参数化和验证逻辑。基础版 3 天左右可以跑通，5 天可以把校验、报告和演示效果做得更完整。
```

如果被问亮点：

```text
亮点主要是可信生成和自主验证。它不是简单地让 AI 直接写 ATK 命令，而是把生成过程拆成结构化任务、参数校验、模板生成和验证报告几个环节。这样可以减少幻觉，提升可解释性，也方便后续扩展更多 ATK 功能。
```

---

## 15. 当前需要立即做的事

下一步建议：

1. 在 `D:\Shana Program\文档\Chat` 下创建 Demo 项目目录。
2. 先实现不依赖 API 的本地规则版。
3. 把 Connect 案例改造成 Jinja2 模板。
4. 定义 `inclination_change_transfer` 的 JSON Schema。
5. 写一个命令行入口：

```text
python app.py "创建一个倾角改变轨道机动规划场景……"
```

6. 输出：

```text
generated/generated_connect_inclination_change.py
generated/structured_task.json
generated/validation_report.md
```

7. 如果时间允许，再接 OpenAI API。

---

## 16. 最小可交付效果

即使不调用真实 ATK，也应做到：

1. 用户输入自然语言。
2. 系统输出结构化任务 JSON。
3. 系统输出可读执行计划。
4. 系统生成 Connect Python 二次开发代码。
5. 系统输出自主验证报告。
6. 报告明确说明当前是代码级验证还是真实 ATK 执行验证。

这就已经满足：

```text
可行：能从自然语言走到二次开发代码。
可信：不是自由生成，而是 Schema + 模板 + 验证。
有亮点：自主验证报告、缺参追问、后端可扩展。
```

---

## 17. 关键原则

最终 Demo 应围绕这句话展开：

> AI 负责理解和规划，程序负责约束、生成和验证。

不要把重点放在“大模型多聪明”，而要放在：

1. 如何降低幻觉风险。
2. 如何保证生成代码可信。
3. 如何让用户确认系统理解。
4. 如何让 ATK 二次开发能力可被自然语言调用。
5. 如何逐步扩展更多业务模板。

---

## 18. 如果需要新会话继续

如果当前 Codex 对话因额度、登录方式或 API Key 切换中断，新会话可以直接读取本文件，并从以下任务继续：

```text
请基于 D:\Shana Program\文档\Chat\ATK自然语言二次开发Demo交接文档.md，帮我实现一个 ATK Connect 自然语言二次开发代码生成与自主验证 Demo。
```

建议新会话继续时的第一步：

1. 创建项目目录 `atk_nl_codegen_demo`。
2. 从 Connect 案例提取模板。
3. 实现 `app.py`。
4. 生成示例代码和验证报告。

---

## 19. 2026-07-26 运行验证更新

当前项目已经完成外部 Python 运行验证：

```text
generated/generated_connect_inclination_change.py
→ 导入 ATKConnectModule
→ atkOpen 连接本机 6655 端口
→ atkConnect 逐条发送 Connect 命令
→ ATK 中可以直接看到对应三维模型效果
```

这说明 Demo 已经从“代码级 Dry Run 验证”升级为：

```text
外部 Python → Connect → ATK 实际执行成功
```

当前运行前提：

1. ATK 已启动并监听 `6655` 端口。
2. `generated/` 目录中存在：

```text
ATKConnectModule.py
_ATKConnectModule.pyd
```

3. 生成脚本顶部已包含：

```python
from ATKConnectModule import atkOpen, atkConnect, atkClose
```

后续建议优先补强：

1. 生成脚本记录 Connect 命令执行日志，并在 `NACK` / `FALSE` 时打印警告但不中断，运行结束后输出 `connect_execution_log.json` 和 `connect_execution_log.md`。
2. 增加运行级验证报告，支持展示全部命令或仅筛选 `NACK` 命令。
3. 增加查询类命令，例如 `DoesObjExist`、对象列表、报告输出检查，用于证明 ATK 内部状态确实变化。
4. 将当前简化模板继续向 ATK 帮助文档原始倾角改变案例对齐。
