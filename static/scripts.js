/**
 * Frontend interactions: modals, dark mode, suggestions, PWA and DEV mode.
 */

const modalInfo = document.getElementById("modalInfo");
const modalSettings = document.getElementById("modalSettings");

const openInfoBtn = document.getElementById("openModalInfo");
const closeInfoBtn = document.getElementById("closeModalInfo");
const openSettingsBtn = document.getElementById("openModalSettings");
const closeSettingsBtn = document.getElementById("closeModalSettings");
const offlineIndicator = document.getElementById("offline-indicator");

const DEV_KEY = "devMode";

function setOfflineIndicator(isOffline) {
	if (!offlineIndicator) return;
	offlineIndicator.classList.toggle("d-none", !isOffline);
}

function applyDevModeState() {
	const enabled = localStorage.getItem(DEV_KEY) === "true";
	const panel = document.getElementById("dev-panel");
	const toggleWrap = document.getElementById("dev-mode-toggle-wrap");
	const switcher = document.getElementById("devModeSwitch");
	if (switcher) switcher.checked = enabled;
	if (toggleWrap) toggleWrap.classList.toggle("d-none", !enabled);
	if (panel) panel.classList.toggle("d-none", !enabled);
	return enabled;
}

function enableDevMode() {
	localStorage.setItem(DEV_KEY, "true");
	applyDevModeState();
}

async function loadDevData() {
	if (localStorage.getItem(DEV_KEY) !== "true") return;
	const status = document.getElementById("dev-status");
	if (status) {
		status.textContent = JSON.stringify(window.__SERVER_STATE__ || {}, null, 2);
	}
}

async function loadLogs() {
	const logsEl = document.getElementById("dev-logs");
	if (!logsEl) return;
	try {
		const response = await fetch("/group/logs");
		const payload = await response.json();
		logsEl.textContent = (payload.lines || []).join("\n") || "no logs";
	} catch (error) {
		logsEl.textContent = `log error: ${error}`;
	}
}

if (openInfoBtn && modalInfo) {
	openInfoBtn.onclick = (event) => {
		event.preventDefault();
		modalInfo.style.display = "block";
	};
}

if (closeInfoBtn && modalInfo) {
	closeInfoBtn.onclick = () => {
		modalInfo.style.display = "none";
	};
}

if (openSettingsBtn && modalSettings) {
	openSettingsBtn.onclick = async (event) => {
		event.preventDefault();
		modalSettings.style.display = "block";
		await loadDevData();
	};
}

if (closeSettingsBtn && modalSettings) {
	closeSettingsBtn.onclick = () => {
		modalSettings.style.display = "none";
	};
}

window.addEventListener("click", (event) => {
	if (modalInfo && event.target === modalInfo) {
		modalInfo.style.display = "none";
	}
	if (modalSettings && event.target === modalSettings) {
		modalSettings.style.display = "none";
	}
});

async function refreshScheduleInBackground() {
	const scheduleContent = document.getElementById("schedule-content");
	if (!scheduleContent) return;

	const refreshUrl = scheduleContent.dataset.refreshUrl;
	if (!refreshUrl) return;

	try {
		const response = await fetch(refreshUrl, { method: "GET" });
		const payload = await response.json();
		if (payload?.ok && payload?.html) {
			scheduleContent.innerHTML = payload.html;
			window.__SERVER_STATE__ = {
				...(window.__SERVER_STATE__ || {}),
				offline: !!payload.offline,
				cacheState: payload.cache_state,
				metrics: payload.metrics,
			};
			setOfflineIndicator(!!payload.offline || !navigator.onLine);
		}
	} catch (error) {
		console.warn("Background refresh skipped:", error);
	}
}

function registerServiceWorker() {
	if (!("serviceWorker" in navigator)) return;
	navigator.serviceWorker.register("/static/sw.js").catch((error) => {
		console.warn("Service worker registration failed:", error);
	});
}

function setupDevModeUnlock() {
	const target = document.getElementById("dev-tap-target");
	if (!target) return;

	let taps = [];
	target.addEventListener("click", () => {
		const now = Date.now();
		taps = taps.filter((t) => now - t < 10000);
		taps.push(now);
		if (taps.length >= 10) {
			enableDevMode();
			taps = [];
		}
	});
}

document.addEventListener("DOMContentLoaded", () => {
	const groupInput = document.getElementById("group-input");
	const suggestionsContainer = document.getElementById("suggestions-container");
	const searchForm = document.getElementById("searchForm");
	const darkModeSwitch = document.getElementById("darkModeSwitch");
	const devModeSwitch = document.getElementById("devModeSwitch");
	const loadLogsBtn = document.getElementById("loadLogsBtn");
	const body = document.body;

	let suggestions = [];
	const isDarkMode = localStorage.getItem("darkMode") === "true";
	body.classList.toggle("dark-mode", isDarkMode);
	if (darkModeSwitch) darkModeSwitch.checked = isDarkMode;

	if (darkModeSwitch) {
		darkModeSwitch.addEventListener("change", function () {
			body.classList.toggle("dark-mode", this.checked);
			localStorage.setItem("darkMode", String(this.checked));
		});
	}

	if (devModeSwitch) {
		devModeSwitch.addEventListener("change", function () {
			localStorage.setItem(DEV_KEY, String(this.checked));
			applyDevModeState();
		});
	}

	if (loadLogsBtn) {
		loadLogsBtn.addEventListener("click", () => {
			void loadLogs();
		});
	}

	applyDevModeState();
	setupDevModeUnlock();
	registerServiceWorker();
	setOfflineIndicator((window.__SERVER_STATE__ && window.__SERVER_STATE__.offline) || !navigator.onLine);

	window.addEventListener("online", () => setOfflineIndicator(false));
	window.addEventListener("offline", () => setOfflineIndicator(true));

	void refreshScheduleInBackground();

	fetch("/static/suggestions.json")
		.then((response) => response.json())
		.then((data) => {
			suggestions = data;
		})
		.catch((error) => console.error("Ошибка загрузки подсказок:", error));

	if (!groupInput || !suggestionsContainer || !searchForm) return;

	const lastInput = localStorage.getItem("lastInput");
	if (lastInput) groupInput.value = lastInput;

	groupInput.addEventListener("input", function () {
		const inputValue = this.value.toLowerCase();
		localStorage.setItem("lastInput", this.value);

		if (!inputValue) {
			suggestionsContainer.style.display = "none";
			return;
		}

		const filtered = suggestions
			.filter((item) => item.name.toLowerCase().includes(inputValue))
			.slice(0, 10);

		if (!filtered.length) {
			suggestionsContainer.style.display = "none";
			return;
		}

		suggestionsContainer.innerHTML = "";
		filtered.forEach((suggestion) => {
			const item = document.createElement("a");
			item.className = "list-group-item list-group-item-action";

			let badgeColor = "primary";
			if (suggestion.type === "Teacher") badgeColor = "success";
			else if (suggestion.type === "Classroom") badgeColor = "info";

			item.innerHTML = `${suggestion.name} <span class="badge rounded-pill bg-${badgeColor} badge-type">${suggestion.type}</span>`;
			item.href = "#";
			item.addEventListener("click", (event) => {
				event.preventDefault();
				groupInput.value = suggestion.name;
				suggestionsContainer.style.display = "none";
				localStorage.setItem("lastInput", suggestion.name);
				localStorage.setItem("lastGroup", suggestion.name);
				searchForm.submit();
			});
			suggestionsContainer.appendChild(item);
		});

		suggestionsContainer.style.display = "block";
	});

	groupInput.addEventListener("blur", () => {
		setTimeout(() => {
			suggestionsContainer.style.display = "none";
		}, 200);
	});

	groupInput.addEventListener("focus", () => {
		if (groupInput.value.length > 0 && suggestionsContainer.children.length > 0) {
			suggestionsContainer.style.display = "block";
		}
	});

	document.addEventListener("click", (event) => {
		if (!suggestionsContainer.contains(event.target) && event.target !== groupInput) {
			suggestionsContainer.style.display = "none";
		}
	});
});
