const requestInput = document.querySelector("#request-input");
const taskTypeSelect = document.querySelector("#task-type-select");
const taskTypeDescription = document.querySelector("#task-type-description");
const parseButton = document.querySelector("#parse-button");
const executeButton = document.querySelector("#execute-button");
const loadSampleButton = document.querySelector("#load-sample");
const expertToggle = document.querySelector("#expert-toggle");
const expertSection = document.querySelector("#expert-section");
const statusLine = document.querySelector("#status-line");
const structuredTask = document.querySelector("#structured-task");
const timeUnderstanding = document.querySelector("#time-understanding");
const readinessReport = document.querySelector("#readiness-report");
const generatedCode = document.querySelector("#generated-code");
const generatedFilePath = document.querySelector("#generated-file-path");
const executionOutput = document.querySelector("#execution-output");
const clarificationBox = document.querySelector("#clarification-box");
const followUpInput = document.querySelector("#follow-up-input");
const followUpSubmit = document.querySelector("#follow-up-submit");
const logSummary = document.querySelector("#log-summary");
const logInsight = document.querySelector("#log-insight");
const logTable = document.querySelector("#log-table");
const helpDialog = document.querySelector("#help-dialog");
const helpTitle = document.querySelector("#help-title");
const helpBody = document.querySelector("#help-body");
const closeHelpButton = document.querySelector("#close-help");

let currentLogs = [];
let currentFilter = "all";
let taskTypes = [];
let hasExecutedCurrentCode = false;
let latestTask = null;

loadSampleButton.addEventListener("click", loadSample);
parseButton.addEventListener("click", parseRequest);
executeButton.addEventListener("click", executeLatestCode);
closeHelpButton.addEventListener("click", () => helpDialog.close());
followUpSubmit.addEventListener("click", submitTimeFollowUp);
expertToggle.addEventListener("click", toggleExpertSection);
taskTypeSelect.addEventListener("change", () => {
  renderTaskTypeDescription();
  loadSample();
  executeButton.disabled = true;
});

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".filter").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    currentFilter = button.dataset.filter;
    renderLogs();
  });
});

loadTaskTypes();

async function loadTaskTypes() {
  const response = await fetch("/api/task-types");
  const data = await response.json();
  taskTypes = data.task_types || [];
  taskTypeSelect.innerHTML = "";
  taskTypes.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.label;
    taskTypeSelect.append(option);
  });
  renderTaskTypeDescription();
  await loadSample();
}

function renderTaskTypeDescription() {
  const selected = taskTypes.find((item) => item.id === taskTypeSelect.value);
  taskTypeDescription.textContent = selected ? selected.description : "请选择任务类型。";
}

async function loadSample() {
  const query = new URLSearchParams({ task_type: taskTypeSelect.value });
  const response = await fetch(`/api/sample?${query.toString()}`);
  const data = await response.json();
  requestInput.value = data.request;
}

async function parseRequest() {
  const request = requestInput.value.trim();
  if (!request) {
    statusLine.textContent = "请先输入自然语言任务。";
    return;
  }

  statusLine.textContent = "正在解析自然语言并生成代码...";
  parseButton.disabled = true;

  try {
    const response = await fetch("/api/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ request, task_type: taskTypeSelect.value }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "解析失败");
    }

    latestTask = data.structured_task;
    structuredTask.textContent = JSON.stringify(data.structured_task, null, 2);
    timeUnderstanding.textContent = JSON.stringify(data.time_understanding, null, 2);
    renderReadinessReport(data);
    generatedCode.textContent = data.generated_code;
    generatedFilePath.textContent = `本次写入：${data.files.generated_code}；同时更新 latest：${data.files.latest_generated_code}`;
    executionOutput.textContent = "代码已生成，确认 ATK 已启动并监听 6655 端口后，可点击“确认执行最新代码”。";
    hasExecutedCurrentCode = false;
    clearDisplayedLogs("本次代码尚未执行，暂无执行日志。");
    executeButton.disabled = false;
    renderClarification(data.clarification, data.structured_task);
    statusLine.textContent = `生成完成，验证状态：${data.status}`;
  } catch (error) {
    statusLine.textContent = `发生错误：${error.message}`;
  } finally {
    parseButton.disabled = false;
  }
}

function renderReadinessReport(data) {
  const task = data.structured_task || {};
  const errors = data.task_errors || [];
  const warnings = data.task_warnings || [];
  const codeFailed = data.code_failed || [];
  const canExecute = errors.length === 0 && codeFailed.length === 0;

  readinessReport.innerHTML = "";
  const status = document.createElement("div");
  status.className = `readiness-status ${canExecute ? "ok" : "warn"}`;
  status.textContent = canExecute ? "可以生成并尝试执行" : "需要先处理问题";
  readinessReport.append(status);

  const plainSummary = document.createElement("div");
  plainSummary.className = "plain-summary";
  plainSummary.innerHTML = `<p class="summary-title">本次任务将做什么</p>${describeTaskInPlainLanguage(task)}`;
  readinessReport.append(plainSummary);

  const summary = document.createElement("div");
  summary.className = "readiness-grid";
  summary.append(
    buildReadinessItem("任务", getTaskLabel(task.intent)),
    buildReadinessItem("场景", task.scenario_name || "未识别"),
    buildReadinessItem("对象", describeObjects(task)),
    buildReadinessItem("时间", describeTimePeriod(task)),
  );
  readinessReport.append(summary);

  const checks = document.createElement("div");
  checks.className = "readiness-checks";
  checks.append(
    buildCheckLine(errors.length === 0, errors.length === 0 ? "任务参数已通过基础检查" : `发现 ${errors.length} 个参数问题`),
    buildCheckLine(codeFailed.length === 0, codeFailed.length === 0 ? "生成代码包含必要步骤" : `生成代码缺少 ${codeFailed.length} 个关键步骤`),
    buildCheckLine(warnings.length === 0, warnings.length === 0 ? "没有明显默认假设需要注意" : `有 ${warnings.length} 条注意事项，见下方说明`),
  );
  readinessReport.append(checks);

  const friendlyNotes = buildFriendlyNotes(task, warnings);
  if (warnings.length || errors.length || codeFailed.length || friendlyNotes.length) {
    const detail = document.createElement("ul");
    detail.className = "readiness-detail";
    [...errors, ...codeFailed.map((item) => `生成代码缺少：${item}`), ...friendlyNotes]
      .slice(0, 5)
      .forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        detail.append(li);
      });
    readinessReport.append(detail);
  }

  const nextStep = document.createElement("p");
  nextStep.className = "readiness-next";
  nextStep.textContent = canExecute
    ? "确认 ATK 已启动并开启 6655 端口后，可以点击“确认执行最新代码”。"
    : "请根据上面的提示补充或修改自然语言输入，然后重新生成。";
  readinessReport.append(nextStep);
}

function buildReadinessItem(label, value) {
  const item = document.createElement("div");
  item.className = "readiness-item";
  item.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>`;
  return item;
}

function buildCheckLine(ok, text) {
  const item = document.createElement("p");
  item.className = `check-line ${ok ? "ok" : "warn"}`;
  item.textContent = `${ok ? "通过" : "注意"}：${text}`;
  return item;
}

function getTaskLabel(intent) {
  const selected = taskTypes.find((item) => item.id === intent);
  return selected ? selected.label : intent || "未识别";
}

function describeObjects(task) {
  if (task.satellites?.length) {
    return `${task.satellites.length} 颗卫星：${task.satellites.map((item) => item.name).join("、")}`;
  }
  if (task.facilities?.length) {
    return `${task.facilities.length} 个地面站：${task.facilities.map((item) => item.name).join("、")}`;
  }
  return task.satellite_name || "未识别";
}

function describeTimePeriod(task) {
  if (!task.time_period?.start || !task.time_period?.end) {
    return "未确认";
  }
  return `${task.time_period.start} 至 ${task.time_period.end}`;
}

function describeTaskInPlainLanguage(task) {
  if (task.intent === "satellite_orbit_visualization") {
    const satellites = task.satellites || [];
    const items = satellites.map((satellite) => `<li>${escapeHtml(describeSatellite(satellite))}</li>`).join("");
    return `
      <p>系统将创建 ${satellites.length} 颗卫星，并在 ATK 中显示轨道。</p>
      <ul>${items || "<li>尚未识别到卫星参数。</li>"}</ul>
      <p>仿真时间：${escapeHtml(describeTimePeriod(task))}</p>
    `;
  }
  if (task.intent === "ground_facility_setup") {
    const facilities = task.facilities || [];
    const items = facilities
      .map((facility) => `<li>${escapeHtml(facility.name)}：纬度 ${formatValue(facility.latitude?.value)}°，经度 ${formatValue(facility.longitude?.value)}°，高度 ${formatValue(facility.altitude?.value)} m</li>`)
      .join("");
    return `
      <p>系统将在 ATK 中创建地面站。</p>
      <ul>${items || "<li>尚未识别到地面站参数。</li>"}</ul>
      <p>仿真时间：${escapeHtml(describeTimePeriod(task))}</p>
    `;
  }
  if (task.intent === "satellite_facility_access") {
    return `
      <p>系统将创建卫星和地面站，并计算二者在分析时间内的可见性。</p>
      <p>对象：${escapeHtml(describeObjects(task))}</p>
      <p>仿真时间：${escapeHtml(describeTimePeriod(task))}</p>
    `;
  }
  if (task.intent === "inclination_change_transfer") {
    return `
      <p>系统将创建一颗卫星，并使用 Astrogator 执行倾角改变机动规划。</p>
      <p>初始轨道：半长轴 ${formatValue(task.initial_orbit?.sma?.value)} m，偏心率 ${formatValue(task.initial_orbit?.ecc)}，倾角 ${formatValue(task.initial_orbit?.inc?.value)}°。</p>
      <p>目标：远地点 ${formatValue(task.targets?.apoapsis_radius?.value)} m，最终倾角 ${formatValue(task.targets?.final_inclination?.value)}°。</p>
      <p>仿真时间：${escapeHtml(describeTimePeriod(task))}</p>
    `;
  }
  return `<p>系统将按所选任务模板生成 ATK Connect 脚本。</p>`;
}

function describeSatellite(satellite) {
  const heightKm = satellite?.sma?.value ? (Number(satellite.sma.value) - 6371000) / 1000 : null;
  const heightText = heightKm === null ? "高度未识别" : `高度约 ${formatValue(heightKm)} km`;
  return `${satellite.name}：${heightText}，倾角 ${formatValue(satellite.inc?.value)}°，偏心率 ${formatValue(satellite.ecc)}（0 表示近似圆轨道）`;
}

function buildFriendlyNotes(task, warnings) {
  const notes = [];
  (task.assumptions || []).forEach((assumption) => {
    notes.push(rewriteAssumptionForUser(assumption));
  });
  warnings.forEach((warning) => {
    if (warning.includes("RunMCS")) {
      notes.push("本任务会运行 Astrogator 机动规划计算。执行前请确认初始轨道、目标约束和时间范围符合预期。");
    } else if (warning.includes("未明确识别字段")) {
      notes.push("有些信息没有在输入中明确说明，系统已使用默认值。可以在自然语言中补充后重新生成。");
    } else {
      notes.push(warning);
    }
  });
  return [...new Set(notes)];
}

function rewriteAssumptionForUser(text) {
  if (text.includes("未明确识别开始时间")) {
    return "你没有明确指定开始时间，系统暂时使用默认开始时间。可以在输入中补充“从明天上午9点开始”。";
  }
  if (text.includes("未指定结束时间") && text.includes("一圈")) {
    return "你没有指定结束时间，系统按第一颗卫星的轨道周期估算运行一圈所需时间。";
  }
  if (text.includes("未指定场景名")) {
    return "你没有指定场景名，系统使用默认场景名。";
  }
  if (text.includes("未指定卫星名")) {
    return "你没有指定卫星名，系统使用默认卫星名。";
  }
  return text.replaceAll("未识别", "没有明确识别到").replaceAll("使用默认值", "暂时使用默认值");
}

function buildExecutionConfirmMessage(task) {
  if (!task) {
    return "确认执行最近一次生成的 Connect Python 代码？请先确保 ATK 已启动并开启 6655 端口。";
  }
  return [
    "即将连接本机 ATK，并执行刚生成的任务：",
    "",
    `任务：${getTaskLabel(task.intent)}`,
    `场景：${task.scenario_name || "未识别"}`,
    `对象：${describeObjects(task)}`,
    `时间：${describeTimePeriod(task)}`,
    "",
    "请先确保 ATK 已启动，并且 Connect 端口为 6655。",
    "是否继续？",
  ].join("\n");
}

function renderLogInsight(summary) {
  const nackCount = Number(summary.nack || 0);
  if (nackCount > 0) {
    logInsight.textContent = `发现 ${nackCount} 条 NACK 命令。可在下方筛选“只看 NACK”，并点击“查看帮助”定位对应 ATK 文档。`;
    logInsight.className = "log-insight warn";
    return;
  }
  if (Number(summary.total || 0) > 0) {
    logInsight.textContent = "本次执行没有发现 NACK 命令。";
    logInsight.className = "log-insight ok";
    return;
  }
  logInsight.textContent = "本次代码尚未执行，暂无排错信息。";
  logInsight.className = "log-insight";
}

function formatValue(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "未识别";
  }
  if (Math.abs(number) >= 100000) {
    return number.toExponential(3);
  }
  return Number.isInteger(number) ? String(number) : number.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

async function executeLatestCode() {
  const confirmed = window.confirm(buildExecutionConfirmMessage(latestTask));
  if (!confirmed) {
    return;
  }

  executeButton.disabled = true;
  parseButton.disabled = true;
  statusLine.textContent = "正在执行最新生成代码，请等待 ATK 响应...";
  executionOutput.textContent = "正在执行 generated_connect_latest.py ...";

  try {
    const response = await fetch("/api/execute-latest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "执行失败");
    }

    const lines = [
      `脚本：${data.script}`,
      `退出码：${data.returncode}`,
      `状态：${data.success ? "执行完成" : "执行过程存在错误"}`,
      "",
      "----- STDOUT -----",
      data.stdout || "<empty>",
      "",
      "----- STDERR -----",
      data.stderr || "<empty>",
    ];
    executionOutput.textContent = lines.join("\n");
    hasExecutedCurrentCode = true;
    statusLine.textContent = data.success ? "执行完成，已刷新执行日志。" : "执行完成但退出码非 0，请查看输出。";
    await loadLogs();
  } catch (error) {
    executionOutput.textContent = `执行失败：${error.message}`;
    statusLine.textContent = `执行失败：${error.message}`;
  } finally {
    executeButton.disabled = false;
    parseButton.disabled = false;
  }
}

async function toggleExpertSection() {
  const isHidden = expertSection.classList.toggle("hidden");
  expertToggle.textContent = isHidden ? "展开详细信息" : "收起详细信息";
  if (!isHidden) {
    if (hasExecutedCurrentCode) {
      await loadLogs();
    } else {
      clearDisplayedLogs("本次代码尚未执行，暂无执行日志。");
    }
  }
}

function renderClarification(clarification, task) {
  if (!clarification) {
    clarificationBox.textContent = "暂无追问信息";
    setFollowUpEnabled(false);
    return;
  }

  if (clarification.kind === "time_identified") {
    clarificationBox.innerHTML = "";
    appendTextBlock(clarificationBox, "DeepSeek 时间解释", clarification.note);
    appendTimePeriodBlock(clarificationBox, task);
    setFollowUpEnabled(false);
    return;
  }

  if (clarification.kind === "time_missing") {
    clarificationBox.innerHTML = "";
    const note = document.createElement("p");
    note.textContent = clarification.note;
    clarificationBox.append(note);

    const question = document.createElement("p");
    question.textContent = clarification.questions?.[0] || "请补充时间。";
    clarificationBox.append(question);

    const choiceWrap = document.createElement("div");
    choiceWrap.className = "choice-row";
    (clarification.choices || []).forEach((choice) => {
      const button = document.createElement("button");
      button.className = "secondary";
      button.textContent = choice.label;
      button.addEventListener("click", () => applyTimeFollowUp(choice.text));
      choiceWrap.append(button);
    });
    clarificationBox.append(choiceWrap);
    appendTimePeriodBlock(clarificationBox, task);

    followUpInput.placeholder = clarification.custom_placeholder || "补充时间，例如：持续三天";
    setFollowUpEnabled(true);
    return;
  }

  const lines = [
    `状态：${clarification.enabled ? "已启用" : "预留中"}`,
    `说明：${clarification.note}`,
    "",
    "建议追问：",
    ...clarification.questions.map((item) => `- ${item}`),
  ];

  if (clarification.assumptions?.length) {
    lines.push("", "默认假设：");
    lines.push(...clarification.assumptions.map((item) => `- ${item}`));
  }

  clarificationBox.textContent = lines.join("\n");
  setFollowUpEnabled(false);
}

function appendTextBlock(parent, title, text) {
  const titleEl = document.createElement("p");
  titleEl.className = "clarification-title";
  titleEl.textContent = title;
  const textEl = document.createElement("p");
  textEl.textContent = text || "暂无说明。";
  parent.append(titleEl, textEl);
}

function appendTimePeriodBlock(parent, task) {
  const timePeriod = task?.time_period;
  if (!timePeriod?.start || !timePeriod?.end) {
    return;
  }

  const box = document.createElement("div");
  box.className = "time-period-summary";
  box.innerHTML = `
    <p class="clarification-title">将设置到 ATK 的分析时间</p>
    <p><strong>开始：</strong>${escapeHtml(timePeriod.start)}</p>
    <p><strong>结束：</strong>${escapeHtml(timePeriod.end)}</p>
  `;
  parent.append(box);
}

function setFollowUpEnabled(enabled) {
  followUpInput.disabled = !enabled;
  followUpSubmit.disabled = !enabled;
  if (!enabled) {
    followUpInput.value = "";
  }
}

async function submitTimeFollowUp() {
  const text = followUpInput.value.trim();
  if (!text) {
    statusLine.textContent = "请先填写要补充的时间信息。";
    return;
  }
  await applyTimeFollowUp(text);
}

async function applyTimeFollowUp(text) {
  requestInput.value = `${requestInput.value.trim()}，${text}`;
  statusLine.textContent = `已补充时间：${text}，正在重新解析...`;
  await parseRequest();
}

async function loadLogs() {
  const response = await fetch("/api/logs");
  const data = await response.json();
  currentLogs = data.logs || [];
  const summary = data.summary || { total: 0, nack: 0, ok: 0 };
  logSummary.textContent = `总数 ${summary.total}，NACK ${summary.nack}，OK ${summary.ok}`;
  renderLogInsight(summary);

  if (data.message) {
    logTable.textContent = data.message;
    return;
  }

  renderLogs();
}

function clearDisplayedLogs(message) {
  currentLogs = [];
  logSummary.textContent = "本次尚未执行";
  logInsight.textContent = "本次代码尚未执行，暂无排错信息。";
  logInsight.className = "log-insight";
  logTable.textContent = message;
}

function renderLogs() {
  const logs = currentLogs.filter((item) => currentFilter === "all" || item.status === currentFilter);
  if (!logs.length) {
    logTable.textContent = "当前筛选条件下没有日志。";
    return;
  }

  logTable.innerHTML = "";
  logs.forEach((item) => {
    const row = document.createElement("div");
    row.className = `log-row ${item.status}`;

    const meta = document.createElement("div");
    meta.className = "log-meta";
    meta.innerHTML = `
      <span>第 ${item.step} 步 · <strong>${escapeHtml(item.command)}</strong></span>
      <span class="badge ${item.status}">${item.status.toUpperCase()}</span>
    `;

    const commandLine = document.createElement("div");
    commandLine.className = "command-line";
    commandLine.textContent = `${item.command} | ${item.cmd_string} | 返回：${item.result || "<empty>"}`;

    row.append(meta, commandLine);

    if (item.status === "nack") {
      const helpButton = document.createElement("button");
      helpButton.className = "help-button";
      helpButton.textContent = "查看帮助";
      helpButton.addEventListener("click", () => openHelp(item));
      row.append(helpButton);
    }

    logTable.append(row);
  });
}

async function openHelp(item) {
  const query = new URLSearchParams({
    command: item.command,
    cmd_string: item.cmd_string,
  });
  const response = await fetch(`/api/help?${query.toString()}`);
  const help = await response.json();

  helpTitle.textContent = help.title;
  const examples = help.examples?.length
    ? `<ul>${help.examples.map((example) => `<li><code>${escapeHtml(example)}</code></li>`).join("")}</ul>`
    : "<p>暂无示例。</p>";
  const hints = help.troubleshooting_hints?.length
    ? `<ul>${help.troubleshooting_hints.map((hint) => `<li>${escapeHtml(hint)}</li>`).join("")}</ul>`
    : "<p>暂无排错建议。</p>";

  helpBody.innerHTML = `
    <p><strong>语法：</strong><code>${escapeHtml(help.syntax)}</code></p>
    <p><strong>文档状态：</strong>${help.exists ? "已定位到本地帮助页" : "未找到本地帮助页，请检查 ATK 帮助目录路径"}</p>
    <p><strong>帮助页：</strong></p>
    <p class="help-path">${escapeHtml(help.doc_path)}</p>
    <p>
      <button class="secondary" id="open-help-local">打开帮助页面</button>
      <button class="secondary" id="copy-help-path">复制路径</button>
    </p>
    <h4>示例</h4>
    ${examples}
    <h4>排错提示</h4>
    ${hints}
    <p class="status-line">如果浏览器阻止打开 file:// 链接，请复制路径后在浏览器地址栏或资源管理器中打开。</p>
  `;

  helpDialog.showModal();
  document.querySelector("#copy-help-path").addEventListener("click", async () => {
    await navigator.clipboard.writeText(help.doc_path);
    statusLine.textContent = "已复制帮助页路径。";
  });
  document.querySelector("#open-help-local").addEventListener("click", async () => {
    await openHelpWithSystem(item);
  });
}

async function openHelpWithSystem(item) {
  const response = await fetch("/api/open-help", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      command: item.command,
      cmd_string: item.cmd_string,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    statusLine.textContent = data.error || "打开帮助页失败。";
    return;
  }
  statusLine.textContent = `已请求系统打开帮助页：${data.doc_path}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
