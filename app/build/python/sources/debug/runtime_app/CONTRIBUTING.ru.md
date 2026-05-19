# Участие в разработке APKLife (RU)

## 1) Подготовка окружения
### Linux/macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## 2) Локальный запуск
```bash
make run
```

## 3) Проверки качества
```bash
make test
make lint
```

## 4) Стратегия ветвления
- Ветки от `main` в формате `feature/<topic>` или `fix/<topic>`.
- Коммиты — небольшие и атомарные.
- Перед PR делайте rebase на `origin/main`.

## 5) Ожидания от pull request
- Описать мотивацию и технический подход.
- Приложить команды валидации и результат.
- Обновить документацию при изменении поведения/конфига.
- Не коммитить секреты/токены.

## 6) Ожидания по коду
- Форматирование Black.
- Проход Ruff и Mypy.
- Сервисные модули с единой ответственностью.
- Без wildcard-импортов.

## 7) Полезные ссылки
- Основная документация: [README.ru.md](README.ru.md)
- Архитектура: [docs/ARCHITECTURE.ru.md](docs/ARCHITECTURE.ru.md)
- Кодекс поведения: [CODE_OF_CONDUCT.ru.md](CODE_OF_CONDUCT.ru.md)
