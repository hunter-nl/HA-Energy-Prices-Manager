const tableBody = document.querySelector("#periods-table tbody");
const addBtn = document.getElementById("add-row");
const saveBtn = document.getElementById("save-btn");
const resetBtn = document.getElementById("reset-btn");
const infoCard = document.getElementById("current-info");
const statusMessage = document.getElementById("status-message");

const API_BASE_PATH = "api";

let periods = [];
let originalPeriods = [];
let translations = {};
let translationCatalog = {};
let language = "en";
let activePeriod = null;
let hasLoadedPeriods = false;

function t(key, replacements = {}) {
  let value = translations[key] ?? key;
  Object.entries(replacements).forEach(([name, replacement]) => {
    value = value.replaceAll(`{${name}}`, replacement);
  });
  return value;
}

function homeAssistantLanguage() {
  try {
    return window.parent.document.documentElement.lang || navigator.language;
  } catch (error) {
    console.warn("Unable to read the Home Assistant language", error);
    return navigator.language;
  }
}

function languageCode() {
  return homeAssistantLanguage()?.toLowerCase().startsWith("nl") ? "nl" : "en";
}

function applyTranslations(allTranslations) {
  language = languageCode();
  translationCatalog = allTranslations;
  translations = allTranslations[language] ?? allTranslations.en;
  document.documentElement.lang = language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  if (hasLoadedPeriods) {
    renderTable();
    renderCurrentInfo(activePeriod);
  }
}

async function loadTranslations() {
  const response = await fetch("translations.json");
  if (!response.ok) throw new Error("Unable to load translations.");
  applyTranslations(await response.json());
}

function observeHomeAssistantLanguage() {
  try {
    const root = window.parent.document.documentElement;
    new MutationObserver(() => {
      const nextLanguage = languageCode();
      if (nextLanguage !== language) applyTranslations(translationCatalog);
    }).observe(root, { attributes: true, attributeFilter: ["lang"] });
  } catch (error) {
    console.warn("Unable to observe the Home Assistant language", error);
  }
}

// Listen for system theme changes (when HA theme changes)
const darkModePreference = window.matchMedia("(prefers-color-scheme: dark)");
darkModePreference.addEventListener("change", (e) => {
  // Trigger CSS update by forcing a reflow
  document.documentElement.style.colorScheme = e.matches ? "dark" : "light";
});

function setStatus(message, type = "info") {
  statusMessage.textContent = message;
  statusMessage.className = type;
}

function formatCurrency(value) {
  return Number(value).toLocaleString(language, {
    minimumFractionDigits: 5,
    maximumFractionDigits: 5,
  });
}

function validatePeriod(period, index) {
  const errors = [];
  if (!period.start) errors.push(t("row_start_required", { row: index + 1 }));
  if (!period.end) errors.push(t("row_end_required", { row: index + 1 }));
  if (period.start && period.end && period.start > period.end) {
    errors.push(t("row_date_order", { row: index + 1 }));
  }
  if (!Number.isFinite(period.import_t1)) {
    errors.push(t("row_import_t1_invalid", { row: index + 1 }));
  }
  if (!Number.isFinite(period.import_t2)) {
    errors.push(t("row_import_t2_invalid", { row: index + 1 }));
  }
  if (!Number.isFinite(period.export_t1)) {
    errors.push(t("row_export_t1_invalid", { row: index + 1 }));
  }
  if (!Number.isFinite(period.export_t2)) {
    errors.push(t("row_export_t2_invalid", { row: index + 1 }));
  }
  if (!Number.isFinite(period.gas) || period.gas < 0) {
    errors.push(t("row_gas_invalid", { row: index + 1 }));
  }
  return errors;
}

function hasOverlap(newStart, newEnd, idx) {
  const start = new Date(newStart);
  const end = new Date(newEnd);
  return periods.some((p, i) => {
    if (i === idx || !p.start || !p.end) return false;
    return start <= new Date(p.end) && end >= new Date(p.start);
  });
}

function validateAllPeriods() {
  const errors = [];
  periods.forEach((period, index) => {
    errors.push(...validatePeriod(period, index));
  });
  periods.forEach((period, index) => {
    if (
      period.start &&
      period.end &&
      hasOverlap(period.start, period.end, index)
    ) {
      errors.push(t("row_overlap", { row: index + 1 }));
    }
  });
  return errors;
}

function getTableData() {
  return Array.from(tableBody.rows).map((row) => {
    const [start, end, import_t1, import_t2, export_t1, export_t2, gas] = Array.from(
      row.querySelectorAll("input"),
    ).map((input) => input.value);
    return {
      start,
      end,
      import_t1: parseFloat(import_t1),
      import_t2: parseFloat(import_t2),
      export_t1: parseFloat(export_t1),
      export_t2: parseFloat(export_t2),
      gas: parseFloat(gas),
    };
  });
}

function dataChanged() {
  const current = getTableData();
  if (current.length !== originalPeriods.length) return true;
  for (let i = 0; i < current.length; i += 1) {
    const a = current[i];
    const b = originalPeriods[i];
    if (
      a.start !== b.start ||
      a.end !== b.end ||
      a.import_t1 !== b.import_t1 ||
      a.import_t2 !== b.import_t2 ||
      a.export_t1 !== b.export_t1 ||
      a.export_t2 !== b.export_t2 ||
      a.gas !== b.gas
    ) {
      return true;
    }
  }
  return false;
}

function updateSaveButton() {
  saveBtn.disabled = !dataChanged();
}

function renderCurrentInfo(active) {
  activePeriod = active;
  infoCard.replaceChildren();
  if (!active || active.detail) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = t("no_active_period");
    infoCard.appendChild(emptyState);
    return;
  }
  const rows = [
    [t("active_period"), `${active.start} → ${active.end}`],
    [t("import_electricity_t1"), `€${formatCurrency(active.import_t1)}`],
    [t("import_electricity_t2"), `€${formatCurrency(active.import_t2)}`],
    [t("export_electricity_t1"), `€${formatCurrency(active.export_t1)}`],
    [t("export_electricity_t2"), `€${formatCurrency(active.export_t2)}`],
    [t("gas"), `€${formatCurrency(active.gas)}`],
  ];
  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "info-row";
    const heading = document.createElement("strong");
    heading.textContent = label;
    row.append(heading, document.createTextNode(value));
    infoCard.appendChild(row);
  });
}

function createInput(type, value, label, minimum = "-1") {
  const input = document.createElement("input");
  input.type = type;
  input.value = value ?? "";
  input.setAttribute("aria-label", label);
  if (type === "number") {
    input.step = "0.00001";
    input.min = minimum;
  }
  return input;
}

function handleTableTab(event) {
  if (event.key !== "Tab") return;

  const inputs = Array.from(tableBody.querySelectorAll("input"));
  const currentIndex = inputs.indexOf(event.currentTarget);
  const nextIndex = currentIndex + (event.shiftKey ? -1 : 1);

  if (nextIndex >= 0 && nextIndex < inputs.length) {
    event.preventDefault();
    inputs[nextIndex].focus();
  }
}

function renderTable() {
  tableBody.replaceChildren();
  const now = new Date();
  periods.forEach((period, index) => {
    const tr = document.createElement("tr");
    const startDate = period.start ? new Date(period.start) : null;
    const endDate = period.end ? new Date(period.end) : null;

    if (startDate && endDate && now >= startDate && now <= endDate) {
      tr.classList.add("current-period");
    }

    const inputs = [
      createInput("date", period.start, t("aria_start_date")),
      createInput("date", period.end, t("aria_end_date")),
      createInput("number", period.import_t1, t("aria_import_t1_price")),
      createInput("number", period.import_t2, t("aria_import_t2_price")),
      createInput("number", period.export_t1, t("aria_export_t1_price")),
      createInput("number", period.export_t2, t("aria_export_t2_price")),
      createInput("number", period.gas, t("aria_gas_price"), "0"),
    ];
    const columns = [
      { className: "date-column", label: t("start_date") },
      { className: "date-column", label: t("end_date") },
      { className: "price-column", label: t("import_electricity_t1_price") },
      { className: "price-column", label: t("import_electricity_t2_price") },
      { className: "price-column", label: t("export_electricity_t1_price") },
      { className: "price-column", label: t("export_electricity_t2_price") },
      { className: "price-column", label: t("gas_price") },
    ];
    inputs.forEach((input, columnIndex) => {
      const cell = document.createElement("td");
      cell.className = columns[columnIndex].className;
      cell.dataset.label = columns[columnIndex].label;
      cell.appendChild(input);
      tr.appendChild(cell);
    });

    const deleteCell = document.createElement("td");
    deleteCell.className = "actions-column";
    const deleteButton = document.createElement("button");
    deleteButton.className = "delete";
    deleteButton.type = "button";
    deleteButton.title = t("delete_row");
    deleteButton.textContent = "🗑️";
    deleteCell.appendChild(deleteButton);
    tr.appendChild(deleteCell);

    const keys = [
      "start",
      "end",
      "import_t1",
      "import_t2",
      "export_t1",
      "export_t2",
      "gas",
    ];
    inputs.forEach((input, i) => {
      input.addEventListener("keydown", handleTableTab);
      input.addEventListener("input", () => {
        periods[index][keys[i]] =
          input.type === "number" ? parseFloat(input.value) : input.value;
        if (
          (keys[i] === "start" || keys[i] === "end") &&
          periods[index].start &&
          periods[index].end
        ) {
          if (hasOverlap(periods[index].start, periods[index].end, index)) {
            setStatus(t("overlap_error"), "error");
          } else {
            setStatus("", "info");
          }
        }
        updateSaveButton();
      });
    });

    deleteButton.addEventListener("click", () => {
      if (confirm(t("delete_confirm"))) {
        periods.splice(index, 1);
        renderTable();
      }
    });

    tableBody.appendChild(tr);
  });
  updateSaveButton();
}

async function loadPeriods() {
  try {
    const [periodRes, currentRes] = await Promise.all([
      fetch(`${API_BASE_PATH}/periods`),
      fetch(`${API_BASE_PATH}/current`),
    ]);

    if (!periodRes.ok) throw new Error("Unable to load saved periods.");
    periods = await periodRes.json();
    originalPeriods = periods.map((p) => ({ ...p }));
    hasLoadedPeriods = true;
    renderTable();
    renderCurrentInfo(currentRes.ok ? await currentRes.json() : null);
  } catch (error) {
    setStatus(t("load_error"), "error");
    console.error(error);
  }
}

function resetChanges() {
  periods = originalPeriods.map((p) => ({ ...p }));
  renderTable();
  setStatus(t("reset_success"), "info");
}

function sortPeriodsByStart(data) {
  return data.slice().sort((a, b) => a.start.localeCompare(b.start));
}

addBtn.addEventListener("click", () => {
  periods.push({
    start: "",
    end: "",
    import_t1: 0.0,
    import_t2: 0.0,
    export_t1: 0.0,
    export_t2: 0.0,
    gas: 0.0,
  });
  renderTable();
});

resetBtn.addEventListener("click", resetChanges);

saveBtn.addEventListener("click", async () => {
  const data = getTableData();
  const errors = validateAllPeriods();
  if (errors.length > 0) {
    setStatus(errors.join(" "), "error");
    return;
  }

  try {
    const sortedData = sortPeriodsByStart(data);
    const res = await fetch(`${API_BASE_PATH}/periods`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sortedData),
    });

    if (!res.ok) {
      const json = await res.json().catch(() => ({}));
      throw new Error(
        json.detail ? json.detail.join(" ") : "Unable to save periods.",
      );
    }

    periods = sortedData;
    originalPeriods = periods.map((p) => ({ ...p }));
    renderTable();
    setStatus(t("save_success"), "success");
    const currentData = await fetch(`${API_BASE_PATH}/current`).then((r) =>
      r.ok ? r.json() : null,
    );
    renderCurrentInfo(currentData);
  } catch (error) {
    setStatus(error.message || t("save_error"), "error");
    console.error(error);
  }
});

async function initialize() {
  try {
    await loadTranslations();
    observeHomeAssistantLanguage();
  } catch (error) {
    console.error(error);
  }
  await loadPeriods();
}

initialize();
