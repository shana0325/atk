# ATK 自然语言二次开发代码生成 Demo

这是一个用于面试展示的最小闭环 Demo：

```text
用户自然语言
→ 结构化任务 JSON
→ 参数校验
→ 可读执行计划
→ Connect Python 代码生成
→ 自主验证报告
```

核心思想：

> 不让 AI 直接自由生成 ATK Connect 命令，而是先把自然语言转换为受约束的结构化任务，再由程序通过固定模板生成代码并验证。

## 当前支持的任务

当前先支持一个任务模板：

```text
inclination_change_transfer
倾角改变轨道机动规划：低轨 → GEO 远地点抬升 → 圆化 → 倾角降为 0 度
```

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

## 运行方式

在项目目录执行：

```powershell
python app.py "创建一个倾角改变轨道机动规划场景，从2022年11月5日开始，初始半长轴6570000米，倾角28度，远地点到42160000米，最后倾角降到0度"
```

也可以使用示例：

```powershell
python app.py --example
```

运行后会生成：

```text
generated/structured_task.json
generated/execution_plan.md
generated/generated_connect_inclination_change.py
generated/validation_report.md
```

## Demo 亮点

1. **结构化理解**：先输出 JSON 任务，而不是直接吐命令。
2. **参数校验**：检查时间、单位、轨道参数范围和目标约束。
3. **缺参追问**：输入过于模糊时，不盲目执行。
4. **模板生成**：Connect 命令来自固定模板，降低幻觉风险。
5. **自主验证**：生成后检查关键命令和流程是否完整。

## 当前边界

当前版本默认是 Dry Run，不直接连接 ATK。它验证代码生成链路是否可信；如果要真实执行，需要确保 ATK 已启动、Connect 端口开启，并且 `atkOpen`、`atkConnect`、`atkClose` 可用。

