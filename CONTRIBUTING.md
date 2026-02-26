# Contributing to APKLife / Участие в разработке APKLife

## Environment setup / Подготовка окружения
1. Install Python 3.11+ / Установите Python 3.11+.
2. Create virtualenv / Создайте виртуальное окружение: `python -m venv .venv`.
3. Activate virtualenv and install deps / Активируйте окружение и установите зависимости: `make install`.

## Running locally / Локальный запуск
- `make run`
- App opens on / Приложение откроется на `http://127.0.0.1:5000`.

## Running tests / Запуск тестов
- `make test`

## Linting and static checks / Линтинг и статический анализ
- `make lint`

## Branching strategy / Стратегия ветвления
- Branch from `main` using `feature/<topic>` / Создавайте ветки от `main` в формате `feature/<topic>`.
- Keep commits small and focused / Делайте небольшие и сфокусированные коммиты.
- Rebase on top of `origin/main` before PR / Перед PR обновляйте ветку через rebase на `origin/main`.

## Pull request rules / Правила pull request
- Provide motivation + technical summary / Добавляйте мотивацию и техническое описание.
- Include test/lint output / Прикладывайте результаты тестов и линтинга.
- Do not merge with failing CI / Не мержите PR при падающем CI.

## Code style expectations / Ожидания по стилю кода
- Use Black formatting / Используйте форматирование Black.
- Keep functions small and single-purpose / Делайте функции небольшими и с одной ответственностью.
- No wildcard imports / Без wildcard-импортов.
- Add type hints in service layer / Добавляйте type hints в сервисном слое.
