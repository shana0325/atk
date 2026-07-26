const requestInput = document.querySelector("#request-input");
const taskTypeSelect = document.querySelector("#task-type-select");
const taskTypeDescription = document.querySelector("#task-type-description");
const parseButton = document.querySelector("#parse-button");
const executeButton = document.querySelector("#execute-button");
const loadSampleButton = document.querySelector("#load-sample");
const refreshLogsButton = document.querySelector("#refresh-logs");
const statusLine = document.querySelector("#status-line");
const structuredTask = document.querySelector("#structured-task");
const executionPlan = document.querySelector("#execution-plan");
const timeUnderstanding = document.querySelector("#time-understanding");
const validationReport = document.querySelector("#validation-report");
const generatedCode = document.querySelector("#generated-code");
const generatedFilePath = document.querySelector("#generated-file-path");
const executionOutput = document.querySelector("#execution-output");
const clarificationBox = document.querySelector("#clarification-box");
const logSummary = document.querySelector("#log-summary");
const logTable = document.querySelector("#log-table");
const helpDialog = document.querySelector("#help-dialog");
const helpTitle = document.querySelector("#help-title");
const helpBody = document.querySelector("#help-body");
const closeHelpButton = document.querySelector("#close-help");

let currentLogs = [];
let currentFilter = "all";
let taskTypes = [];

loadSampleButton.addEventListener("click", loadSample);
parseButton.addEventListener("click", parseRequest);
executeButton.addEventListener("click", executeLatestCode);
refreshLogsButton.addEventListener("click", loadLogs);
closeHelpButton.addEventListener("click", () => helpDialog.close());
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
loadLogs();

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

    structuredTask.textContent = JSON.stringify(data.structured_task, null, 2);
    executionPlan.textContent = data.execution_plan;
    timeUnderstanding.textContent = JSON.stringify(data.time_understanding, null, 2);
    validationReport.textContent = data.validation_report;
    generatedCode.textContent = data.generated_code;
    generatedFilePath.textContent = `本次写入：${data.files.generated_code}；同时更新 latest：${data.files.latest_generated_code}`;
    executionOutput.textContent = "代码已生成，确认 ATK 已启动并监听 6655 端口后，可点击“确认执行最新代码”。";
    executeButton.disabled = false;
    renderClarification(data.clarification);
    statusLine.textContent = `生成完成，验证状态：${data.status}`;
  } catch (error) {
    statusLine.textContent = `发生错误：${error.message}`;
  } finally {
    parseButton.disabled = false;
  }
}

async function executeLatestCode() {
  const confirmed = window.confirm("确认执行最近一次生成的 Connect Python 代码？请先确保 ATK 已启动并开启 6655 端口。");
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

function renderClarification(clarification) {
  if (!clarification) {
    clarificationBox.textContent = "暂无追问信息";
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
}

async function loadLogs() {
  const response = await fetch("/api/logs");
  const data = await response.json();
  currentLogs = data.logs || [];
  const summary = data.summary || { total: 0, nack: 0, ok: 0 };
  logSummary.textContent = `总数 ${summary.total}，NACK ${summary.nack}，OK ${summary.ok}`;

  if (data.message) {
    logTable.textContent = data.message;
    return;
  }

  renderLogs();
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
      <a href="${help.doc_url}" target="_blank" rel="noreferrer">打开本地帮助页</a>
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
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
