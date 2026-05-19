/**
 * APKLife Frontend interactions:
 * Этот файл управляет всеми интерактивными элементами на стороне клиента:
 * 1. Открытие/закрытие модальных диалогов (Settings, Info).
 * 2. Переключение темной/светлой темы с сохранением в localStorage.
 * 3. Автодополнение (Suggestions) при поиске группы.
 * 4. PWA Service Worker для оффлайн режима.
 * 5. Асинхронное фоновое обновление и предзагрузка расписания.
 *
 * Специально для Junior: все функции подробно документированы!
 */

// Получаем ссылки на HTML-элементы диалоговых окон
const modalInfo = document.getElementById("modalInfo");
const modalSettings = document.getElementById("modalSettings");
const modalStatus = document.getElementById("modalStatus");
const modalUpdate = document.getElementById("modalUpdate");

// Получаем кнопки для открытия/закрытия диалоговых окон
const openInfoBtn = document.getElementById("openModalInfo");
const closeInfoBtn = document.getElementById("closeModalInfo");
const openSettingsBtn = document.getElementById("openModalSettings");
const closeSettingsBtn = document.getElementById("closeModalSettings");
const openStatusBtn = document.getElementById("openModalStatus");
const closeStatusBtn = document.getElementById("closeModalStatus");
const closeUpdateBtn = document.getElementById("closeModalUpdate");
const offlineIndicator = document.getElementById("offline-indicator");

// Ключ для хранения статуса режима разработчика в LocalStorage браузера
const DEV_KEY = "devMode";

/**
 * Функция обновления языка интерфейса.
 * Заменяет параметр "lang" в URL адресе страницы и перезагружает ее.
 */
function updateLanguage(lang) {
	localStorage.setItem("lang", lang);
	const url = new URL(window.location.href);
	url.searchParams.set("lang", lang);
	window.location.href = url.toString();
}

/**
 * Показывает или скрывает плашку "Вы работаете без интернета" вверху страницы.
 * Теперь учитывает переключатель имитации оффлайна (Mock Offline Switch).
 */
function setOfflineIndicator(isOffline) {
	if (!offlineIndicator) return;
	const mockOffline = document.getElementById("mockOfflineSwitch")?.checked;
	offlineIndicator.classList.toggle("d-none", !(isOffline || mockOffline));
}

/**
 * Применяет режим разработчика.
 * Если режим активен: показывает отладочную DEV-панель с техническим состоянием.
 */
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

/**
 * Активирует режим разработчика в LocalStorage.
 */
function enableDevMode() {
	localStorage.setItem(DEV_KEY, "true");
	applyDevModeState();
}

/**
 * Загружает технические данные о состоянии сервера в DEV-панель.
 */
async function loadDevData() {
	if (localStorage.getItem(DEV_KEY) !== "true") return;
	const status = document.getElementById("dev-status");
	if (status) {
		// Выводим серверное состояние в читаемом формате JSON
		status.textContent = JSON.stringify(window.__SERVER_STATE__ || {}, null, 2);
	}
}

/**
 * Подгружает системные логи с сервера для удобного дебага прямо в интерфейсе!
 */
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

/**
 * Универсальные функции для открытия и закрытия модальных диалогов (MD3 Dialogs).
 * Они также управляют классом 'active', чтобы подсветить активную вкладку в меню (активные пилюли).
 */
function showModal(modal, btnMobile) {
	if (!modal) return;
	modal.style.display = "block";
	if (btnMobile) btnMobile.classList.add("active");
    document.body.dataset.isModalOpen = "true";
}

/**
 * Закрывает модальное окно.
 */
function hideModal(modal, btnMobile) {
	if (!modal) return;
	modal.style.display = "none";
	if (btnMobile) btnMobile.classList.remove("active");
    document.body.dataset.isModalOpen = "false";
}

// Привязываем обработчики клика для открытия/закрытия диалога "О проекте"
if (openInfoBtn && modalInfo) {
	openInfoBtn.onclick = (event) => {
		event.preventDefault();
		showModal(modalInfo, openInfoBtn);
	};
}

if (closeInfoBtn && modalInfo) {
	closeInfoBtn.onclick = () => {
		hideModal(modalInfo, openInfoBtn);
	};
}

// Привязываем обработчики клика для открытия/закрытия диалога "Настройки"
if (openSettingsBtn && modalSettings) {
	openSettingsBtn.onclick = async (event) => {
		event.preventDefault();
		showModal(modalSettings, openSettingsBtn);
		await loadDevData();
	};
}

if (closeSettingsBtn && modalSettings) {
	closeSettingsBtn.onclick = () => {
		hideModal(modalSettings, openSettingsBtn);
	};
}

// Привязываем обработчики клика для открытия/закрытия диалога "Статус"
if (openStatusBtn && modalStatus) {
    openStatusBtn.onclick = (event) => {
        event.preventDefault();
        showModal(modalStatus, openStatusBtn);
    };
}

if (closeStatusBtn && modalStatus) {
    closeStatusBtn.onclick = () => {
        hideModal(modalStatus, openStatusBtn);
    };
}

if (closeUpdateBtn && modalUpdate) {
    closeUpdateBtn.onclick = () => {
        hideModal(modalUpdate);
    };
}

// Закрытие модалок при клике на полупрозрачный фон снаружи диалога
window.addEventListener("click", (event) => {
	if (modalInfo && event.target === modalInfo) {
		hideModal(modalInfo, openInfoBtn);
	}
	if (modalSettings && event.target === modalSettings) {
		hideModal(modalSettings, openSettingsBtn);
	}
    if (modalStatus && event.target === modalStatus) {
        hideModal(modalStatus, openStatusBtn);
    }
    if (modalUpdate && event.target === modalUpdate) {
        hideModal(modalUpdate);
    }
});

/**
 * Проверка обновлений через GitHub API (через наш прокси-роут)
 */
async function checkUpdates() {
    try {
        const response = await fetch("/version");
        const data = await response.json();

        if (data.is_update_available) {
            const statusText = document.getElementById("update-status-text");
            if (statusText) statusText.textContent = data.status_text;
            showModal(modalUpdate);
        }
    } catch (error) {
        console.warn("Update check failed:", error);
    }
}

/**
 * Асинхронное фоновое обновление расписания.
 * Запрашивает актуальные данные у сервера в фоновом режиме, не мешая пользователю,
 * и мягко обновляет HTML-контент страницы, если данные изменились.
 */
async function refreshScheduleInBackground() {
	const scheduleContent = document.getElementById("schedule-content");
	if (!scheduleContent) return;

	const refreshUrl = scheduleContent.dataset.refreshUrl;
	if (!refreshUrl) return;

	try {
		const response = await fetch(refreshUrl, { method: "GET" });
		const payload = await response.json();
		if (payload?.ok && payload?.html) {
			// Обновляем разметку расписания без перезагрузки всей страницы!
			scheduleContent.innerHTML = payload.html;

			// Синхронизируем глобальные переменные состояния сервера
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

/**
 * Умный механизм предзагрузки соседних недель (Prefetching).
 * Когда пользователь заходит на текущую неделю, скрипт с задержкой в 1.2 секунды
 * отправляет фоновые запросы на предзагрузку предыдущей и следующей недель.
 * Сервер кэширует эти данные, поэтому при клике на стрелки переключение происходит МГНОВЕННО!
 */
async function prefetchNeighborWeeks() {
	const urlParams = new URLSearchParams(window.location.search);
	const groupName = urlParams.get("group_name");
	if (!groupName) return;

	let weekId = parseInt(urlParams.get("week_id"));
	if (isNaN(weekId)) {
		return;
	}

	const lang = urlParams.get("lang") || "ru";

	// Вычисляем URL соседних недель
	const prevUrl = `/group/refresh?group_name=${encodeURIComponent(groupName)}&week_id=${weekId - 1}&lang=${lang}`;
	const nextUrl = `/group/refresh?group_name=${encodeURIComponent(groupName)}&week_id=${weekId + 1}&lang=${lang}`;

	// Запускаем предзагрузку с задержкой, чтобы не нагружать канал при старте
	setTimeout(() => {
		void fetch(prevUrl).catch(() => {});
		void fetch(nextUrl).catch(() => {});
	}, 1200);
}

/**
 * Регистрация Service Worker для PWA-функционала.
 * Позволяет приложению открываться оффлайн, сохраняя структуру в кэш браузера.
 */
function registerServiceWorker() {
	if (!("serviceWorker" in navigator)) return;
	navigator.serviceWorker.register("/static/sw.js").catch((error) => {
		console.warn("Service worker registration failed:", error);
	});
}

/**
 * Секретная функция ("Пасхалка"): активация режима разработчика.
 * Если быстро кликнуть 10 раз по надписи внизу страницы Info, откроется DEV-режим!
 */
function setupDevModeUnlock() {
	const target = document.getElementById("dev-tap-target");
	if (!target) return;

	let taps = [];
	target.addEventListener("click", () => {
		const now = Date.now();
		// Очищаем клики, сделанные более 10 секунд назад
		taps = taps.filter((t) => now - t < 10000);
		taps.push(now);

		// Если за 10 секунд сделано 10 кликов — активируем режим разработчика!
		if (taps.length >= 10) {
			enableDevMode();
			taps = [];
		}
	});
}

/**
 * Главный инициализатор страницы. Запускается, когда DOM полностью загружен.
 */
document.addEventListener("DOMContentLoaded", () => {
	const groupInput = document.getElementById("group-input");
	const suggestionsContainer = document.getElementById("suggestions-container");
	const searchForm = document.getElementById("searchForm");
	const darkModeSwitch = document.getElementById("darkModeSwitch");
	const devModeSwitch = document.getElementById("devModeSwitch");
	const loadLogsBtn = document.getElementById("loadLogsBtn");
	const languageSelect = document.getElementById("languageSelect");
	
	// DEV-инструменты
	const clearDevCacheBtn = document.getElementById("clearDevCacheBtn");
	const mockOfflineSwitch = document.getElementById("mockOfflineSwitch");
	const pingDevServerBtn = document.getElementById("pingDevServerBtn");
	const pingResult = document.getElementById("ping-result");
	const pingDownloadServerBtn = document.getElementById("pingDownloadServerBtn");
	const downloadResult = document.getElementById("download-result");
	
	const body = document.body;
	let suggestions = [];

	// Проверяем и восстанавливаем сохраненный статус темной темы из LocalStorage
	const isDarkMode = localStorage.getItem("darkMode") === "true";
	body.classList.toggle("dark-mode", isDarkMode);
	if (darkModeSwitch) darkModeSwitch.checked = isDarkMode;

	// Слушатель переключения темной темы
	if (darkModeSwitch) {
		darkModeSwitch.addEventListener("change", function () {
			body.classList.toggle("dark-mode", this.checked);
			localStorage.setItem("darkMode", String(this.checked));
		});
	}

	// Слушатель включения DEV-режима
	if (devModeSwitch) {
		devModeSwitch.addEventListener("change", function () {
			localStorage.setItem(DEV_KEY, String(this.checked));
			applyDevModeState();
		});
	}

	// Кнопка подгрузки логов
	if (loadLogsBtn) {
		loadLogsBtn.addEventListener("click", () => {
			void loadLogs();
		});
	}

	// Выбор языка интерфейса
	if (languageSelect) {
		languageSelect.addEventListener("change", function () {
			updateLanguage(this.value);
		});
	}

	// 1. Очистка кэша LocalStorage
	if (clearDevCacheBtn) {
		clearDevCacheBtn.addEventListener("click", () => {
			localStorage.clear();
			alert("Локальный кэш (LocalStorage) успешно очищен!");
			window.location.reload();
		});
	}

	// 2. Имитация оффлайн режима
	if (mockOfflineSwitch) {
		mockOfflineSwitch.addEventListener("change", function () {
			setOfflineIndicator(this.checked || (window.__SERVER_STATE__ && window.__SERVER_STATE__.offline) || !navigator.onLine);
		});
	}

	// 3. Замер пинга до сервера
	if (pingDevServerBtn && pingResult) {
		pingDevServerBtn.addEventListener("click", async () => {
			pingResult.textContent = "Замеряем пинг...";
			pingResult.className = "dev-status text-info";
			const start = Date.now();
			try {
				await fetch("/?ping=1");
				const latency = Date.now() - start;
				pingResult.textContent = `Связь с сервером установлена! Пинг: ${latency}мс`;
				pingResult.className = "dev-status text-success";
			} catch (error) {
				pingResult.textContent = `Ошибка пинга: ${error.message}`;
				pingResult.className = "dev-status text-danger";
			}
		});
	}

	// 4. Замер скачивания расписания
	if (pingDownloadServerBtn && downloadResult) {
		pingDownloadServerBtn.addEventListener("click", async () => {
			downloadResult.textContent = "Скачивание расписания...";
			downloadResult.className = "dev-status text-info";
			const start = Date.now();
			try {
				const urlParams = new URLSearchParams(window.location.search);
				const groupName = urlParams.get("group_name") || "11 нмо";
				const weekId = urlParams.get("week_id") || "";
				const lang = urlParams.get("lang") || "ru";
				
				const response = await fetch(`/group/refresh?group_name=${encodeURIComponent(groupName)}&week_id=${weekId}&lang=${lang}`);
				const payload = await response.json();
				const latency = Date.now() - start;
				
				const size = JSON.stringify(payload).length;
				let sizeStr = size + " B";
				if (size > 1024) {
					sizeStr = (size / 1024).toFixed(1) + " KB";
				}
				downloadResult.textContent = `Успешно! Размер: ${sizeStr}, Задержка: ${latency}мс`;
				downloadResult.className = "dev-status text-success";
			} catch (error) {
				downloadResult.textContent = `Ошибка скачивания: ${error.message}`;
				downloadResult.className = "dev-status text-danger";
			}
		});
	}

	// Инициализируем системные вспомогательные утилиты
	applyDevModeState();
	setupDevModeUnlock();
	registerServiceWorker();

	// Устанавливаем статус оффлайна при первой загрузке
	setOfflineIndicator((window.__SERVER_STATE__ && window.__SERVER_STATE__.offline) || !navigator.onLine);

	// Слушаем события изменения статуса сети браузера
	window.addEventListener("online", () => setOfflineIndicator(false));
	window.addEventListener("offline", () => setOfflineIndicator(true));

	// Запускаем фоновые оптимизации
	void refreshScheduleInBackground();
	void prefetchNeighborWeeks();
    void checkUpdates();

	// Загружаем список групп для автодополнения (поисковые предложения)
	fetch("/static/suggestions.json")
		.then((response) => response.json())
		.then((data) => {
			suggestions = data;
		})
		.catch((error) => console.error("Suggestions loading error:", error));

	// Если мы не на главной странице, а на странице расписания (где нет строки поиска) - выходим
	if (!groupInput || !suggestionsContainer || !searchForm) return;

	// Подставляем последний успешный поисковый запрос пользователя для удобства
	const lastInput = localStorage.getItem("lastInput");
	if (lastInput) groupInput.value = lastInput;

	// Логика фильтрации и показа подсказок при вводе в текстовое поле
	groupInput.addEventListener("input", function () {
		const inputValue = this.value.toLowerCase();
		localStorage.setItem("lastInput", this.value);

		if (!inputValue) {
			suggestionsContainer.style.display = "none";
			return;
		}

		// Фильтруем массив подсказок и выводим не более 10 наиболее близких результатов
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

			// Стилизуем бейджи подсказок в зависимости от их типа (Студент, Преподаватель, Аудитория)
			let badgeColor = "primary";
			if (suggestion.type === "Teacher") badgeColor = "success";
			else if (suggestion.type === "Classroom") badgeColor = "info";

			item.innerHTML = `${suggestion.name} <span class="badge rounded-pill bg-${badgeColor} badge-type">${suggestion.type}</span>`;
			item.href = "#";

			// При клике на подсказку — подставляем текст и сразу отправляем форму!
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

	// Скрываем подсказки при потере фокуса (с небольшой задержкой, чтобы успел пройти клик)
	groupInput.addEventListener("blur", () => {
		setTimeout(() => {
			suggestionsContainer.style.display = "none";
		}, 200);
	});

	// Показываем подсказки при фокусе, если там уже есть текст
	groupInput.addEventListener("focus", () => {
		if (groupInput.value.length > 0 && suggestionsContainer.children.length > 0) {
			suggestionsContainer.style.display = "block";
		}
	});

	// Скрываем подсказки при клике в любое свободное место экрана
	document.addEventListener("click", (event) => {
		if (!suggestionsContainer.contains(event.target) && event.target !== groupInput) {
			suggestionsContainer.style.display = "none";
		}
	});
});
