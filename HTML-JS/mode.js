const KEYBOARD = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["a", "z", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["q", "s", "d", "f", "g", "h", "j", "k", "l", "m"],
    ["w", "x", "c", "v", "b", "n", ",", ";", ":", "="],
];

let cursorPollTimer = null;

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
        loadBinds();
    } else if (mode === "CONSOLE") {
        startCursorPoll();
    }
}

// --- Binds editor ---
async function loadBinds() {
    try {
        const res = await fetch("/binds");
        document.getElementById("binds-editor").value = await res.text();
    } catch (ex) {
        setBindsStatus("Failed to load: " + ex.message, true);
    }
}

document.getElementById("binds-reload").addEventListener("click", loadBinds);

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
activateTab("BINDS");
