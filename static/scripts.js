const modalInfo = document.getElementById("modalInfo");
const modalSettings = document.getElementById("modalSettings");

const openInfoBtn = document.getElementById("openModalInfo");
const closeInfoBtn = document.getElementById("closeModalInfo");
const openSettingsBtn = document.getElementById("openModalSettings");
const closeSettingsBtn = document.getElementById("closeModalSettings");

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
	openSettingsBtn.onclick = (event) => {
		event.preventDefault();
		modalSettings.style.display = "block";
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

document.addEventListener("DOMContentLoaded", () => {
	const groupInput = document.getElementById("group-input");
	const suggestionsContainer = document.getElementById("suggestions-container");
	const searchForm = document.getElementById("searchForm");
	const darkModeSwitch = document.getElementById("darkModeSwitch");
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
