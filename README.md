# APKLife 📱🦠

[![License](https://img.shields.io/github/license/drakkoshkka/APKLife?style=flat-square)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/drakkoshkka/APKLife?style=flat-square)](https://github.com/drakkoshkka/APKLife/releases)
[![GitHub stars](https://img.shields.io/github/stars/drakkoshkka/APKLife?style=flat-square)](https://github.com/drakkoshkka/APKLife/stargazers)

**APKLife** — это мобильное Android-приложение, сочетающее в себе веб-технологии (HTML/CSS/JavaScript) и возможности нативной платформы. Проект представляет собой нативное приложение для Android устройств, позволяющее просматривать рассписание в более удобной форме.

---

## 🚀 Особенности

* **Кроссплатформенная веб-основа:** Интерфейс и логика написаны на HTML5, CSS3 и JavaScript.
* **Нативная производительность:** Обернуто в APK для работы на устройствах Android.
* **Легковесность:** Минимальный размер итогового пакета и экономное потребление ресурсов.
* **Интуитивный интерфейс:** Адаптивный дизайн, оптимизированный под экраны мобильных устройств.

## 🛠 Стек технологий

* **Frontend:** HTML, CSS, JavaScript (ES6+)
* **Сборка / Обертка:** Android System WebView
* **Среда сборки:** Android SDK / Gradle

---

## 📦 Инструкция по установке (для пользователей)

Если вы просто хотите установить готовое приложение на свой Android-смартфон:

1. Перейдите в раздел [Releases](https://github.com/drakkoshkka/APKLife/releases).
2. Скачайте актуальный `.apk` файл.
3. Разрешите в настройках устройства установку приложений из неизвестных источников (если это требуется).
4. Откройте скачанный файл на телефоне и следуйте инструкциям установщика.

---

## 🏗 Инструкция по сборке (для разработчиков)

Чтобы развернуть проект локально, внести изменения и собрать собственный APK-файл, следуйте шагам ниже.

### Требования
Перед началом убедитесь, что у вас установлены:
* [Android Studio](https://developer.android.com/studio) и настроенный **Android SDK**

### 1. Клонирование репозитория
```bash
git clone https://github.com/drakkoshkka/APKLife.git
cd APKLife
```
### 2. Сборка Android-проекта и генерация APK
```bash
./gradlew assembleDebug
```
После успешного завершения сборки ваш .apk файл будет находиться по пути:
platforms/android/app/build/outputs/apk/debug/app-debug.apk

### Лицензия
Этот проект распространяется под лицензией MIT. Подробности смотрите в файле LICENSE.
