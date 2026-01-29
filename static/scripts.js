document.addEventListener("DOMContentLoaded", function () {
	const groupInput = document.getElementById("group-input");
	const suggestionsContainer = document.getElementById(
		"suggestions-container"
	);
	const searchForm = document.getElementById("searchForm");
	const darkModeSwitch =
		document.getElementById("darkModeSwitch");
	const autoLoadSwitch =
		document.getElementById("autoLoadSwitch");
	const body = document.body;

	let suggestions = [];

	const isDarkMode =
		localStorage.getItem("darkMode") === "true";
	const autoLoad =
		localStorage.getItem("autoLoad") !== "false";

	// Инициализация темы
	if (isDarkMode) {
		body.classList.add("dark-mode");
		if (darkModeSwitch) darkModeSwitch.checked = true;
	} else {
		body.classList.remove("dark-mode");
		if (darkModeSwitch) darkModeSwitch.checked = false;
	}

	// Инициализация автозагрузки
	if (autoLoadSwitch) {
		autoLoadSwitch.checked = autoLoad;

		autoLoadSwitch.addEventListener("change", function () {
			localStorage.setItem("autoLoad", this.checked);
		});
	}

	// Сохранение выбранной группы
	if (groupInput) {
		groupInput.addEventListener("blur", function () {
			if (this.value.trim()) {
				localStorage.setItem(
					"lastGroup",
					this.value.trim()
				);
			}
		});
	}

	// Предотвращаем перезагрузку при выборе подсказки
	if (searchForm && groupInput) {
		searchForm.addEventListener("submit", function (e) {
			if (groupInput.dataset.selectedSuggestion) {
				e.preventDefault();
				this.submit();
			}
		});
	}

	// Загрузка подсказок
	fetch("/suggestions.json")
		.then((response) => response.json())
		.then((data) => {
			suggestions = data;
		})
		.catch((error) =>
			console.error("Ошибка загрузки подсказок:", error)
		);

	// Логика автодополнения
	if (groupInput && suggestionsContainer) {
		const lastInput = localStorage.getItem("lastInput");
		if (lastInput) {
			groupInput.value = lastInput;
		}

		groupInput.addEventListener("input", function () {
			const inputValue = this.value.toLowerCase();
			localStorage.setItem("lastInput", this.value);

			if (!inputValue.length) {
				suggestionsContainer.style.display = "none";
				return;
			}

			suggestionsContainer.style.display = "block";
			suggestionsContainer.innerHTML = "";

			const filteredSuggestions = suggestions.filter((s) =>
				s.name.toLowerCase().includes(inputValue)
			);

			if (filteredSuggestions.length > 10) {
				suggestionsContainer.classList.add(
					"suggestions-container-scrollable"
				);
			} else {
				suggestionsContainer.classList.remove(
					"suggestions-container-scrollable"
				);
			}

			filteredSuggestions
				.slice(0, 15)
				.forEach((suggestion) => {
					const item = document.createElement("a");
					item.classList.add(
						"list-group-item",
						"list-group-item-action"
					);
					item.href = "#";

					let badgeColor = "primary";
					if (suggestion.type === "Teacher")
						badgeColor = "success";
					else if (suggestion.type === "Classroom")
						badgeColor = "info";

					item.innerHTML = `
					${suggestion.name}
					<span class="badge rounded-pill bg-${badgeColor} badge-type">
						${suggestion.type}
					</span>
				`;

					item.addEventListener("click", (e) => {
						e.preventDefault();
						groupInput.value = suggestion.name;

						localStorage.setItem(
							"lastInput",
							suggestion.name
						);
						localStorage.setItem(
							"lastGroup",
							suggestion.name
						);

						groupInput.dataset.selectedSuggestion =
							"true";
						suggestionsContainer.style.display =
							"none";
						searchForm.submit();
					});

					suggestionsContainer.appendChild(item);
				});
		});

		groupInput.addEventListener("blur", () => {
			setTimeout(() => {
				suggestionsContainer.style.display = "none";
			}, 200);
		});

		groupInput.addEventListener("focus", () => {
			if (groupInput.value.length > 0) {
				suggestionsContainer.style.display = "block";
			}
		});
	}

	// Закрытие подсказок при клике вне области
	document.addEventListener("click", (e) => {
		if (
			suggestionsContainer &&
			groupInput &&
			!suggestionsContainer.contains(e.target) &&
			e.target !== groupInput
		) {
			suggestionsContainer.style.display = "none";
		}
	});

	// Переключение темы
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
});
