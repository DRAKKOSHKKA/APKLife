/**
 * APKLife Debug & Stress Test Module
 * Изолированный модуль для отладки и тестирования производительности.
 */

const DebugModule = {
    logs: [],
    maxLogs: 100,
    overlayActive: false,
    startTime: Date.now(),
    fps: 0,
    frameCount: 0,
    lastFpsUpdate: Date.now(),

    init() {
        console.log("🐞 DebugModule initialized");
        this.loadFlags();
        this.setupOverlay();
        this.setupConsole();
        this.startStatsLoop();
    },

    loadFlags() {
        this.flags = JSON.parse(localStorage.getItem("debug_flags") || '{"newUI": false, "experimentalParser": false, "debugAnimations": false}');
    },

    saveFlags() {
        localStorage.setItem("debug_flags", JSON.stringify(this.flags));
    },

    log(type, message) {
        const entry = {
            time: new Date().toLocaleTimeString(),
            type: type,
            message: message
        };
        this.logs.unshift(entry);
        if (this.logs.length > this.maxLogs) this.logs.pop();
        this.renderLogs();
    },

    setupOverlay() {
        const overlay = document.createElement("div");
        overlay.id = "debug-overlay";
        overlay.style.cssText = "position:fixed; top:10px; left:10px; background:rgba(0,0,0,0.7); color:#0f0; font-family:monospace; font-size:10px; padding:5px; border-radius:4px; z-index:9999; pointer-events:none; display:none;";
        document.body.appendChild(overlay);
        this.overlayElement = overlay;
    },

    setupConsole() {
        const container = document.createElement("div");
        container.id = "debug-console-modal";
        container.className = "cn-modal";
        container.innerHTML = `
            <div class="cn-modal-content bento-modal" style="max-width:800px; height:80vh; display:flex; flex-direction:column;">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="m-0 fw-bold text-primary">DEBUG CONSOLE</h6>
                    <div>
                        <button class="btn btn-sm btn-outline-danger me-2" onclick="DebugModule.clearLogs()">Clear</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="DebugModule.hideConsole()">Close</button>
                    </div>
                </div>
                <div id="debug-logs-container" style="flex-grow:1; overflow-y:auto; background:#111; color:#eee; padding:10px; font-size:12px; border-radius:8px;"></div>
                <div class="mt-2">
                    <input type="text" id="debug-log-filter" class="form-control form-control-sm" placeholder="Filter logs..." oninput="DebugModule.renderLogs()">
                </div>
            </div>
        `;
        document.body.appendChild(container);
        this.consoleElement = container;
    },

    startStatsLoop() {
        const update = () => {
            this.frameCount++;
            const now = Date.now();
            if (now - this.lastFpsUpdate >= 1000) {
                this.fps = Math.round((this.frameCount * 1000) / (now - this.lastFpsUpdate));
                this.frameCount = 0;
                this.lastFpsUpdate = now;
            }

            if (this.overlayActive && this.overlayElement) {
                let memInfo = "N/A";
                if (window.AndroidBridge && window.AndroidBridge.getMemoryInfo) {
                    memInfo = window.AndroidBridge.getMemoryInfo();
                }

                const route = window.location.pathname + window.location.search;
                const netStatus = navigator.onLine ? "Online" : "Offline";
                const mockTime = localStorage.getItem("mock_time_active") === "true" ? " (MOCK)" : "";

                this.overlayElement.innerHTML = `
                    FPS: ${this.fps}<br>
                    MEM: ${memInfo}<br>
                    NET: ${netStatus}<br>
                    TIME: ${new Date().toLocaleTimeString()}${mockTime}<br>
                    ROUTE: ${route}<br>
                    VER: ${window.AndroidBridge ? window.AndroidBridge.getAppVersion() : 'Web'}
                `;
            }
            requestAnimationFrame(update);
        };
        requestAnimationFrame(update);
    },

    toggleOverlay(active) {
        this.overlayActive = active;
        this.overlayElement.style.display = active ? "block" : "none";
        localStorage.setItem("debug_overlay", active);
    },

    showConsole() { this.consoleElement.style.display = "block"; },
    hideConsole() { this.consoleElement.style.display = "none"; },
    clearLogs() { this.logs = []; this.renderLogs(); },

    renderLogs() {
        const container = document.getElementById("debug-logs-container");
        const filter = document.getElementById("debug-log-filter")?.value.toLowerCase() || "";
        if (!container) return;

        container.innerHTML = this.logs
            .filter(l => l.message.toLowerCase().includes(filter) || l.type.toLowerCase().includes(filter))
            .map(l => {
                let color = "#eee";
                if (l.type === "error") color = "#f55";
                if (l.type === "warn") color = "#fa0";
                return `<div style="margin-bottom:4px; border-bottom:1px solid #333; padding-bottom:2px;">
                    <span style="color:#888;">[${l.time}]</span>
                    <span style="color:${color}; font-weight:bold;">${l.type.toUpperCase()}:</span>
                    ${l.message}
                </div>`;
            }).join("");
    },

    // STRESS TESTS
    stressTestUI() {
        this.log("warn", "Starting UI Stress Test: Generating 500 items...");
        const content = document.getElementById("schedule-content") || document.querySelector("main");
        if (!content) return;

        const originalHTML = content.innerHTML;
        let stressHTML = '<div class="alert alert-danger">STRESS TEST MODE: 500 ITEMS</div>';
        for(let i=0; i<500; i++) {
            stressHTML += `
                <div class="lesson mb-2" style="animation: none;">
                    <div class="time">TEST ITEM #${i}</div>
                    <div class="subject">Stress Test Performance Check - Rendering large list of elements</div>
                </div>
            `;
        }
        stressHTML += '<button class="btn btn-primary w-100 mt-3" onclick="location.reload()">Stop Test & Reload</button>';
        content.innerHTML = stressHTML;
    },

    testMemory() {
        this.log("warn", "Starting Memory Test: Allocating memory...");
        let leak = [];
        const interval = setInterval(() => {
            for(let i=0; i<10000; i++) leak.push({text: "Memory leak test data bit " + i, date: new Date()});
            if (leak.length > 500000) {
                clearInterval(interval);
                this.log("error", "Memory Test stopped at 500k objects to prevent crash");
            }
        }, 100);
    }
};

// Auto-init based on storage
document.addEventListener("DOMContentLoaded", () => {
    DebugModule.init();
    if (localStorage.getItem("debug_overlay") === "true") DebugModule.toggleOverlay(true);

    // Intercept console.log
    const oldLog = console.log;
    console.log = function(...args) {
        DebugModule.log("info", args.join(" "));
        oldLog.apply(console, args);
    };

    const oldError = console.error;
    console.error = function(...args) {
        DebugModule.log("error", args.join(" "));
        oldError.apply(console, args);
    };
});
