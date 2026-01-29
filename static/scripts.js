document.addEventListener("DOMContentLoaded", function () {
	const groupInput = document.getElementById("group-input");
	const suggestionsContainer = document.getElementById(
		"suggestions-container"
	);
	const searchForm = document.getElementById("searchForm");
	const darkModeSwitch =
		document.getElementById("darkModeSwitch");
	const body = document.body;

	let suggestions = [];

	// Проверка тёмной темы из localStorage
	const isDarkMode =
		localStorage.getItem("darkMode") === "true";
	if (isDarkMode) {
		body.classList.add("dark-mode");
		if (darkModeSwitch) darkModeSwitch.checked = true;
	} else {
		body.classList.remove("dark-mode");
		if (darkModeSwitch) darkModeSwitch.checked = false;
	}

	// Переключение тёмной темы
	if (darkModeSwitch) {
		darkModeSwitch.addEventListener("change", function () {
			if (this.checked) {
				body.classList.add("dark-mode");
				localStorage.setItem("darkMode", "true");
			} else {
				body.classList.remove("dark-mode");
				localStorage.setItem("darkMode", "false");
			}
		});
	}

	// Загрузка JSON с подсказками
	fetch("/static/suggestions.json")
		.then((response) => response.json())
		.then((data) => {
			suggestions = data;
		})
		.catch((error) =>
			console.error("Ошибка загрузки подсказок:", error)
		);

	if (!groupInput || !suggestionsContainer) return;

	// Восстановление последнего ввода
	const lastInput = localStorage.getItem("lastInput");
	if (lastInput) groupInput.value = lastInput;

	// Ввод текста
	groupInput.addEventListener("input", function () {
		const inputValue = this.value.toLowerCase();
		localStorage.setItem("lastInput", this.value);

		if (!inputValue) {
			suggestionsContainer.style.display = "none";
			return;
		}

		// Фильтруем подсказки и ограничиваем до 10 элементов
		const filtered = suggestions
			.filter((s) =>
				s.name.toLowerCase().includes(inputValue)
			)
			.slice(0, 10);

		if (!filtered.length) {
			suggestionsContainer.style.display = "none";
			return;
		}

		// Очищаем контейнер
		suggestionsContainer.innerHTML = "";

		// Добавляем подсказки
		filtered.forEach((suggestion) => {
			const item = document.createElement("a");
			item.className =
				"list-group-item list-group-item-action";
			let badgeColor = "primary";
			if (suggestion.type === "Teacher")
				badgeColor = "success";
			else if (suggestion.type === "Classroom")
				badgeColor = "info";

			item.innerHTML = `${suggestion.name} <span class="badge rounded-pill bg-${badgeColor} badge-type">${suggestion.type}</span>`;
			item.href = "#";

			item.addEventListener("click", (e) => {
				e.preventDefault();
				groupInput.value = suggestion.name;
				groupInput.dataset.selectedSuggestion = "true";
				suggestionsContainer.style.display = "none";

				localStorage.setItem(
					"lastInput",
					suggestion.name
				);
				localStorage.setItem(
					"lastGroup",
					suggestion.name
				);

				searchForm.submit();
			});

			suggestionsContainer.appendChild(item);
		});

		// Показываем контейнер
		suggestionsContainer.style.display = "block";
	});

	// Скрытие подсказок при потере фокуса
	groupInput.addEventListener("blur", () => {
		setTimeout(
			() => (suggestionsContainer.style.display = "none"),
			200
		);
	});

	// Показ при фокусе
	groupInput.addEventListener("focus", () => {
		if (groupInput.value.length > 0) {
			suggestionsContainer.style.display = "block";
		}
	});

	// Закрытие при клике вне области
	document.addEventListener("click", (e) => {
		if (
			!suggestionsContainer.contains(e.target) &&
			e.target !== groupInput
		) {
			suggestionsContainer.style.display = "none";
		}
	});
});
