/**
 * Глобальный обработчик темы Material 3 (Monet)
 * Принимает объект с CSS переменными и применяет их к :root
 */
window.applyTheme = function(theme) {
    if (!theme) return;
    if (typeof theme === 'string') {
        try { theme = JSON.parse(theme); } catch(e) { console.error(e); return; }
    }

    for (const [key, value] of Object.entries(theme)) {
        if (key === '--is-dark') {
            document.body.classList.toggle('dark-mode', value);
            localStorage.setItem('darkMode', String(value));
        } else {
            document.documentElement.style.setProperty(key, value);
        }
    }
    console.log("Theme applied successfully");
};

// Функция для получения темы из Android
window.getAndroidTheme = function() {
    try {
        if (window.AndroidTheme && window.AndroidTheme.getTheme) {
            const themeJson = window.AndroidTheme.getTheme();
            window.applyTheme(themeJson);
        }
    } catch(e) {
        console.warn("Native theme interface not available:", e);
    }
};

// Применяем тему при загрузке
window.addEventListener('DOMContentLoaded', () => {
    // 1. Если тема пришла через очередь (pendings)
    if (window.__PENDING_THEME__) {
        window.applyTheme(window.__PENDING_THEME__);
        delete window.__PENDING_THEME__;
    }

    // 2. Всегда пробуем запросить у Android
    window.getAndroidTheme();
});
