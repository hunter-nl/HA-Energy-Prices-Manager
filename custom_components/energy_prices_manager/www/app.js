const tableBody = document.querySelector("#periods-table tbody");
const addBtn = document.getElementById("add-row");
const saveBtn = document.getElementById("save-btn");
const resetBtn = document.getElementById("reset-btn");
const infoCard = document.getElementById("current-info");
const statusMessage = document.getElementById("status-message");

const BASE_PATH = (() => {
  const match = window.location.pathname.match(/(.*)\/energy_prices\//);
  return match ? match[1] : "";
})();
const API_BASE = `${BASE_PATH}/api/energy_prices`;

let periods = [];
let originalPeriods = [];

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
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 5,
    maximumFractionDigits: 5,
  });
}

function validatePeriod(period, index) {
  const errors = [];
  if (!period.start) errors.push(`Row ${index + 1}: start date is required.`);
  if (!period.end) errors.push(`Row ${index + 1}: end date is required.`);
  if (period.start && period.end && period.start > period.end) {
    errors.push(`Row ${index + 1}: start date must be on or before end date.`);
  }
  if (!Number.isFinite(period.t1) || period.t1 < 0) {
    errors.push(
      `Row ${index + 1}: low electricity price must be a non-negative number.`,
    );
  }
  if (!Number.isFinite(period.t2) || period.t2 < 0) {
    errors.push(
      `Row ${index + 1}: high electricity price must be a non-negative number.`,
    );
  }
  if (!Number.isFinite(period.gas) || period.gas < 0) {
    errors.push(`Row ${index + 1}: gas price must be a non-negative number.`);
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
      errors.push(`Row ${index + 1}: overlaps with another period.`);
    }
  });
  return errors;
}

function getTableData() {
  return Array.from(tableBody.rows).map((row) => {
    const [start, end, t1, t2, gas] = Array.from(
      row.querySelectorAll("input"),
    ).map((input) => input.value);
    return {
      start,
      end,
      t1: parseFloat(t1),
      t2: parseFloat(t2),
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
      a.t1 !== b.t1 ||
      a.t2 !== b.t2 ||
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
  infoCard.replaceChildren();
  if (!active || active.detail) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = "No active period for today.";
    infoCard.appendChild(emptyState);
    return;
  }
  const rows = [
    ["Active period", `${active.start} → ${active.end}`],
    ["Low electricity", `€${formatCurrency(active.t1)}`],
    ["High electricity", `€${formatCurrency(active.t2)}`],
    ["Gas", `€${formatCurrency(active.gas)}`],
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

function createInput(type, value, label) {
  const input = document.createElement("input");
  input.type = type;
  input.value = value ?? "";
  input.setAttribute("aria-label", label);
  if (type === "number") {
    input.step = "0.00001";
    input.min = "0";
  }
  return input;
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
      createInput("date", period.start, "Start date"),
      createInput("date", period.end, "End date"),
      createInput("number", period.t1, "Low electricity price"),
      createInput("number", period.t2, "High electricity price"),
      createInput("number", period.gas, "Gas price"),
    ];
    inputs.forEach((input) => {
      const cell = document.createElement("td");
      cell.appendChild(input);
      tr.appendChild(cell);
    });

    const deleteCell = document.createElement("td");
    const deleteButton = document.createElement("button");
    deleteButton.className = "delete";
    deleteButton.type = "button";
    deleteButton.title = "Delete row";
    deleteButton.textContent = "🗑️";
    deleteCell.appendChild(deleteButton);
    tr.appendChild(deleteCell);

    const keys = ["start", "end", "t1", "t2", "gas"];
    inputs.forEach((input, i) => {
      input.addEventListener("input", () => {
        periods[index][keys[i]] =
          input.type === "number" ? parseFloat(input.value) : input.value;
        if (
          (keys[i] === "start" || keys[i] === "end") &&
          periods[index].start &&
          periods[index].end
        ) {
          if (hasOverlap(periods[index].start, periods[index].end, index)) {
            setStatus("Overlap detected with another period.", "error");
          } else {
            setStatus("", "info");
          }
        }
        updateSaveButton();
      });
    });

    deleteButton.addEventListener("click", () => {
      if (confirm("Delete this period?")) {
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
      fetch(`${API_BASE}/periods`),
      fetch(`${API_BASE}/current`),
    ]);

    if (!periodRes.ok) throw new Error("Unable to load saved periods.");
    periods = await periodRes.json();
    originalPeriods = periods.map((p) => ({ ...p }));
    renderTable();
    const currentData = currentRes.ok ? await currentRes.json() : null;
    renderCurrentInfo(currentData);
  } catch (error) {
    setStatus("Unable to load period data. Check backend status.", "error");
    console.error(error);
  }
}

function resetChanges() {
  periods = originalPeriods.map((p) => ({ ...p }));
  renderTable();
  setStatus("Changes discarded.", "info");
}

function sortPeriodsByStart(data) {
  return data.slice().sort((a, b) => a.start.localeCompare(b.start));
}

addBtn.addEventListener("click", () => {
  periods.push({ start: "", end: "", t1: 0.0, t2: 0.0, gas: 0.0 });
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
    const res = await fetch(`${API_BASE}/periods`, {
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
    setStatus("Periods saved successfully.", "success");
    const currentData = await fetch(`${API_BASE}/current`).then((r) =>
      r.ok ? r.json() : null,
    );
    renderCurrentInfo(currentData);
  } catch (error) {
    setStatus(error.message || "Error saving periods.", "error");
    console.error(error);
  }
});

loadPeriods();
