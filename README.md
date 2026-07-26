# ATK 自然语言二次开发代码生成 Demo

这是一个用于展示“自然语言使用 ATK”的最小闭环 Demo。

当前 Demo 的核心链路是：

```text
用户选择任务类型
→ 用户自然语言补充参数
→ 结构化任务 JSON
→ 参数校验
→ 可读执行计划
→ 原子 Connect 命令编排 / 受控模板生成
→ Connect Python 代码生成
→ 自主验证报告
→ 外部 Python 连接 ATK 执行
→ Web 页面查看理解结果、执行日志和 NACK 帮助
```

核心思想：

> 不让 AI 直接自由生成 ATK Connect 命令，而是让用户先选择任务类型，AI/规则只负责抽取参数，再由程序进行约束、编排、生成和验证。

## 当前支持的任务

当前网页采用“任务向导”方式，支持以下基础任务类型：

```text
satellite_orbit_visualization
卫星轨道显示：创建一颗或多颗卫星 → SetState Classical 设置轨道 → 显示约一圈轨道
```

```text
ground_facility_setup
地面站创建：创建地面站 → SetPosition Geodetic 设置经纬度和高度
```

```text
satellite_facility_access
卫星-地面站可见性：创建卫星和地面站 → Access 计算二者可见性
```

```text
inclination_change_transfer
倾角改变轨道机动规划：低轨 → GEO 远地点抬升 → 圆化 → 倾角降为 0 度
```

用户在页面上先选任务类型，因此系统不需要在短期 Demo 里承担“任意自然语言自动识别全部 ATK 意图”的风险。

默认示例参数来自已有 ATK Connect Python 案例：

- 场景：`InclinationChange`
- 卫星：`SatInclinationChange`
- 开始时间：`5 Nov 2022 00:00:00.000`
- 结束时间：`8 Nov 2022 00:00:00.000`
- 初始半长轴：`6570000 m`
- 初始偏心率：`0`
- 初始倾角：`28 deg`
- 目标远地点半径：`42160000 m`
- 目标倾角：`0 deg`

## 当前验证状态

当前项目已经完成两类验证：

1. **Dry Run 代码级验证**：可以生成结构化任务、执行计划、Connect Python 代码和自主验证报告。
2. **外部 Python 运行验证**：`generated/generated_connect_inclination_change.py` 已能在 PyCharm/命令行中直接连接 ATK，并在 ATK 中显示对应三维模型效果。

因此当前 Demo 已经不只是“生成代码”，而是已经验证了：

```text
外部 Python → ATK Connect 端口 → ATK 场景/卫星/机动规划效果
```

## 启动 Web 演示页面

在项目目录执行：

```powershell
python web_app.py
```

然后在浏览器打开：

```text
http://127.0.0.1:8765
```

页面中点击“解析并生成代码”后，会生成最近一次任务对应的 Connect Python 代码，并同步更新：

```text
generated/generated_connect_latest.py
```

点击“确认执行最新代码”前，需要确保：

- ATK 已启动。
- Connect 端口为 `6655`。
- `generated/` 目录中已有 `ATKConnectModule.py` 和 `_ATKConnectModule.pyd`。

### 可选：启用 DeepSeek 时间理解

如果要让大模型负责理解“持续三天”“绕 5 圈”“明天开始”这类时间表达，可以配置 DeepSeek API Key。

方式一：PowerShell 临时设置：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
python web_app.py
```

方式二：在项目根目录新建 `.env` 文件：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_MODEL=deepseek-v4-flash
```

`.env` 已在 `.gitignore` 中忽略，不会提交到 Git。

当前网页可以展示：

- 自然语言输入框。
- 任务类型选择框。
- 面向普通用户的时间确认和执行前确认。
- DeepSeek 时间理解结果。
- 当输入中完全没有时间信息时，页面会在时间确认区追问，用户可以补充“持续三天”“绕地球 5 圈”等时间约束并重新生成。
- “确认执行最新代码”按钮，可直接运行 `generated/generated_connect_latest.py`。
- 详细信息区：结构化任务 JSON、DeepSeek 原始返回、生成的 Connect Python 代码、Connect 执行日志筛选。
- `NACK` 命令的“查看帮助”按钮，可定位到预配置的 ATK 本地帮助页。

注意：当前 Demo 中，时间相关自然语言由 DeepSeek 大语言模型理解；卫星高度、倾角、地面站经纬度等其他任务参数仍由规则解析。后续可以把这些参数抽取能力按同样方式迁移到大语言模型，但仍建议保留 Schema、参数校验和固定 Connect 模板生成。

## ATK Connect SDK

```text
D:\Shana\ATK-4.0.1\IntegratingWithATK\connect\Python\ATKConnectModule.py
D:\Shana\ATK-4.0.1\IntegratingWithATK\connect\Python\_ATKConnectModule.pyd
```

当前本地已经复制到：

```text
generated/ATKConnectModule.py
generated/_ATKConnectModule.pyd
```

注意：这两个 SDK 文件属于本机 ATK 安装文件，默认不提交到 Git。

## Demo 亮点

1. **任务向导**：先选任务类型，降低自然语言意图误判风险。
2. **结构化理解**：只在已选任务内抽取参数，再输出 JSON 任务。
3. **DeepSeek 时间理解**：只把“持续三天、绕 5 圈、明天开始”等时间表达抽成受限 JSON，程序再计算结束时间。
4. **参数校验**：检查时间、单位、轨道参数范围、地面站经纬度和目标约束。
5. **原子编排**：多卫星、地面站、可见性任务由 `New`、`SetState`、`SetPosition`、`Access` 等原子命令组合，不为“两颗卫星”单独写死模板。
6. **自主验证**：生成后检查关键命令和流程是否完整。
7. **不中断式执行日志**：生成脚本遇到 `NACK` 会记录警告但继续执行，并输出结构化日志文件。
8. **Web 演示闭环**：页面可查看自然语言理解结果、生成代码、执行日志，并对 `NACK` 命令提供帮助页定位。

## 当前边界

当前版本仍然有一些边界：

- 时间相关表达由 DeepSeek 大语言模型处理，例如“持续三天”“绕 5 圈”“明天开始”。
- 其他任务参数目前仍由规则解析，例如卫星高度、倾角、地面站经纬度、任务对象数量等。
- 后续可以把其他参数抽取也迁移为大语言模型输出结构化 JSON，但仍需要保留 Schema 约束、参数校验和固定 Connect 模板生成。
- 当前时间追问只覆盖“完全没有识别到时间约束”的情况，用户可以在页面中补充时间后重新生成。
- 当前适合演示基础对象创建、轨道显示和简单可见性分析，复杂任务仍需继续扩展能力库。
