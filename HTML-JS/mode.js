const KEYBOARD = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["a", "z", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["q", "s", "d", "f", "g", "h", "j", "k", "l", "m"],
    ["w", "x", "c", "v", "b", "n", ",", ";", ":", "="],
];

let cursorPollTimer = null;
let movesPollTimer = null;
let isUpdatingBindsSelect = false;

// --- Build virtual keyboard grid once ---
(function buildKeyboard() {
    const kbEl = document.getElementById("keyboard");
    KEYBOARD.forEach((row, ri) => {
        const rowEl = document.createElement("div");
        rowEl.className = "kb-row";
        row.forEach((key, ci) => {
            const btn = document.createElement("button");
            btn.className = "kb-key";
            btn.id = `kb-${ri}-${ci}`;
            btn.textContent = key;
            rowEl.appendChild(btn);
        });
        kbEl.appendChild(rowEl);
    });
})();

// --- Tab switching ---
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
        const mode = btn.dataset.mode;
        try {
            await fetch("/setmode?mode=" + mode);
        } catch (ex) {
            console.error("Failed to set mode:", ex);
        }
        activateTab(mode);
    });
});

function activateTab(mode) {
    document.querySelectorAll(".tab-btn").forEach(b =>
        b.classList.toggle("active", b.dataset.mode === mode)
    );
    document.getElementById("panel-binds").classList.toggle("hidden", mode !== "BINDS");
    document.getElementById("panel-console").classList.toggle("hidden", mode !== "CONSOLE");

    if (mode === "BINDS") {
        stopCursorPoll();
        loadBindsOptions();
        loadBinds();
    } else if (mode === "CONSOLE") {
        startCursorPoll();
    }
}

// --- Binds editor ---
async function loadBindsOptions() {
    try {
        const res = await fetch("/binds/options");
        if (!res.ok) {
            throw new Error(await res.text());
        }
        const data = await res.json();
        const select = document.getElementById("binds-file-select");
        const previousValue = select.value;

        isUpdatingBindsSelect = true;
        select.innerHTML = "";
        data.files.forEach(file => {
            const option = document.createElement("option");
            option.value = file;
            option.textContent = file;
            select.appendChild(option);
        });

        if (data.files.includes(data.selected)) {
            select.value = data.selected;
        } else if (data.files.includes(previousValue)) {
            select.value = previousValue;
        }
        isUpdatingBindsSelect = false;
    } catch (ex) {
        isUpdatingBindsSelect = false;
        setBindsStatus("Failed to load bind files: " + ex.message, true);
    }
}

async function loadBinds() {
    try {
        const res = await fetch("/binds");
        document.getElementById("binds-editor").value = await res.text();
    } catch (ex) {
        setBindsStatus("Failed to load: " + ex.message, true);
    }
}

document.getElementById("binds-reload").addEventListener("click", loadBinds);

document.getElementById("binds-file-select").addEventListener("change", async ev => {
    if (isUpdatingBindsSelect) {
        return;
    }
    const selected = ev.target.value;
    try {
        const res = await fetch("/binds/select", { method: "POST", body: selected });
        if (!res.ok) {
            throw new Error(await res.text());
        }
        await loadBinds();
        setBindsStatus("Switched bind file.", false);
    } catch (ex) {
        setBindsStatus("Switch failed: " + ex.message, true);
        await loadBindsOptions();
    }
});

document.getElementById("binds-save").addEventListener("click", async () => {
    const content = document.getElementById("binds-editor").value;
    try {
        const res = await fetch("/binds", { method: "POST", body: content });
        if (res.ok) {
            setBindsStatus("Saved.", false);
        } else {
            setBindsStatus("Save failed: " + await res.text(), true);
        }
    } catch (ex) {
        setBindsStatus("Save failed: " + ex.message, true);
    }
});

function setBindsStatus(msg, isError) {
    const el = document.getElementById("binds-status");
    el.textContent = msg;
    el.className = isError ? "error" : "ok";
    setTimeout(() => { el.textContent = ""; el.className = ""; }, 3000);
}

// --- Move history polling ---
function startMovesPoll() {
    stopMovesPoll();
    pollMovesHistory();
    movesPollTimer = setInterval(pollMovesHistory, 250);
}

function stopMovesPoll() {
    if (movesPollTimer !== null) {
        clearInterval(movesPollTimer);
        movesPollTimer = null;
    }
}

async function pollMovesHistory() {
    try {
        const res = await fetch("/moves/history?limit=80");
        if (!res.ok) {
            return;
        }
        const { moves } = await res.json();
        const el = document.getElementById("moves-history");
        el.value = (moves || []).join(" ");
        el.scrollTop = el.scrollHeight;
    } catch (_) {
        // ignore poll errors silently
    }
}

// --- Virtual keyboard cursor polling ---
function startCursorPoll() {
    stopCursorPoll();
    pollCursor();
    cursorPollTimer = setInterval(pollCursor, 100);
}

function stopCursorPoll() {
    if (cursorPollTimer !== null) {
        clearInterval(cursorPollTimer);
        cursorPollTimer = null;
    }
}

async function pollCursor() {
    try {
        const res = await fetch("/cursor");
        const { row, col, shiftlock } = await res.json();
        updateKeyboard(row, col, shiftlock);
    } catch (_) {
        // ignore poll errors silently
    }
}

function updateKeyboard(row, col, shiftlock) {
    document.querySelectorAll(".kb-key").forEach(k => k.classList.remove("active"));
    const key = document.getElementById(`kb-${row}-${col}`);
    if (key) key.classList.add("active");
    const ind = document.getElementById("shift-indicator");
    ind.textContent = "SHIFT: " + (shiftlock ? "ON" : "OFF");
    ind.className = shiftlock ? "shift-on" : "";
}

// Activate BINDS tab by default on page load
startMovesPoll();
activateTab("BINDS");
