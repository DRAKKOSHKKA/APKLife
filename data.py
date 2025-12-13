import requests
from bs4 import BeautifulSoup

# === Настройки ===
BASE_URL = "https://it-institut.ru/Raspisanie/SearchedRaspisanie"
GROUP_NAME = "11 нмо"
SEARCH_ID = "34745"
OWNER_ID = "37"
WEEK_ID = "14441"

params = {
    "SearchId": SEARCH_ID,
    "SearchString": GROUP_NAME,
    "Type": "Group",
    "OwnerId": OWNER_ID,
    "WeekId": WEEK_ID
}

response = requests.get(BASE_URL, params=params)
response.encoding = "utf-8"

if response.status_code != 200:
    print("Ошибка запроса:", response.status_code)
    exit()

soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")

if not table:
    print("Таблица не найдена!")
    exit()

# === Обработка таблицы ===
rows = table.find_all("tr")
days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

parsed = {}
current_day = "Без дня"  # ← по умолчанию

for row in rows:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if not any(cols):
        continue

    # Проверяем, если строка похожа на день недели
    if len(cols) == 1 and cols[0] in days:
        current_day = cols[0]
        parsed.setdefault(current_day, [])
        continue

    # Если нет, добавляем как урок
    parsed.setdefault(current_day, [])
    parsed[current_day].append([col for col in cols if col])

# === Вывод ===
for day, lessons in parsed.items():
    print(f"\n📅 {day}")
    for i, cols in enumerate(lessons, 1):
        print(f"  {i}. {' | '.join(cols)}")
