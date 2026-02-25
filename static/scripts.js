const modalInfo = document.getElementById("modalInfo");
const modalSettings = document.getElementById("modalSettings");

function bindModal(triggerId, closeId, modalNode) {
	const trigger = document.getElementById(triggerId);
	const closer = document.getElementById(closeId);

	if (trigger && modalNode) {
		trigger.onclick = (e) => {
			e.preventDefault();
			modalNode.style.display = "block";
		};
	}

	if (closer && modalNode) {
		closer.onclick = () => {
			modalNode.style.display = "none";
		};
	}
}

bindModal("openModalInfo", "closeModalInfo", modalInfo);
bindModal("openModalSettings", "closeModalSettings", modalSettings);

window.onclick = (e) => {
	if (modalInfo && e.target === modalInfo) {
		modalInfo.style.display = "none";
	}
	if (modalSettings && e.target === modalSettings) {
		modalSettings.style.display = "none";
	}
};

document.addEventListener("DOMContentLoaded", function () {
	const groupInput = document.getElementById("group-input");
	const suggestionsContainer = document.getElementById("suggestions-container");
	const searchForm = document.getElementById("searchForm");
	const darkModeSwitch = document.getElementById("darkModeSwitch");
	const body = document.body;

	let suggestions = [];

	const isDarkMode = localStorage.getItem("darkMode") === "true";
	body.classList.toggle("dark-mode", isDarkMode);
	if (darkModeSwitch) {
		darkModeSwitch.checked = isDarkMode;
		darkModeSwitch.addEventListener("change", function () {
			body.classList.toggle("dark-mode", this.checked);
			localStorage.setItem("darkMode", this.checked ? "true" : "false");
		});
	}

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
		const inputValue = this.value.toLowerCase().trim();
		localStorage.setItem("lastInput", this.value);

		if (!inputValue) {
			suggestionsContainer.style.display = "none";
			return;
		}

		const filtered = suggestions
			.filter((s) => s.name.toLowerCase().includes(inputValue))
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

			item.addEventListener("click", (e) => {
				e.preventDefault();
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
		setTimeout(() => (suggestionsContainer.style.display = "none"), 200);
	});

	groupInput.addEventListener("focus", () => {
		if (groupInput.value.length > 0 && suggestionsContainer.innerHTML) {
			suggestionsContainer.style.display = "block";
		}
	});

	document.addEventListener("click", (e) => {
		if (!suggestionsContainer.contains(e.target) && e.target !== groupInput) {
			suggestionsContainer.style.display = "none";
		}
	});
});
