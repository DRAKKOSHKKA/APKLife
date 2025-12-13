import requests
from bs4 import BeautifulSoup
import re
import json

def get_group_info(search_string):
    url = "https://it-institut.ru/SearchString/KeySearch"
    params = {
        "Id": 37,
        "SearchProductName": search_string
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = json.loads(response.text)
        if not data:
            return None, None
        for result in data:
            if result.get('SearchContent', '').lower() == search_string.lower():
                return {
                    "SearchId": result.get('SearchId'),
                    "SearchString": result.get('SearchContent'),
                    "OwnerId": result.get('OwnerId'),
                    "Type": result.get('Type')
                }, None
        first_result = data[0]
        return {
            "SearchId": first_result.get('SearchId'),
            "SearchString": first_result.get('SearchContent'),
            "OwnerId": first_result.get('OwnerId'),
            "Type": first_result.get('Type')
        }, first_result.get('SearchContent')
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Ошибка при поиске: {e}")
        return None, None

# utils_schedule.py
# ... остальной код ...

def get_schedule(week_id, entity_info):
    if not entity_info:
        return {}, [], None, None

    search_id = entity_info['SearchId']
    search_string = entity_info['SearchString'].replace(' ', '%20')
    owner_id = entity_info['OwnerId']
    entity_type = entity_info['Type']

    url = f"https://it-institut.ru/Raspisanie/SearchedRaspisanie?SearchId={search_id}&SearchString={search_string}&Type={entity_type}&OwnerId={owner_id}&WeekId={week_id}"
    response = requests.get(url)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    time_headers = []
    header_row = soup.select("thead tr")[0]
    for th in header_row.find_all("th")[1:]:
        colspan = int(th.get('colspan', 1))
        time_text = th.get_text(strip=True)
        for _ in range(colspan):
            time_headers.append(time_text)

    schedule = {}
    days_list = []

    def split_time_interval(time_range, num_parts):
        if not time_range or '-' not in time_range:
            return [time_range] * num_parts
        try:
            start_time, end_time = time_range.split('-')
            start_minutes = time_to_minutes(start_time.strip())
            end_minutes = time_to_minutes(end_time.strip())
            total_minutes = end_minutes - start_minutes
            part_minutes = total_minutes // num_parts
            time_intervals = []
            for i in range(num_parts):
                part_start = start_minutes + i * part_minutes
                part_end = part_start + part_minutes
                time_intervals.append(f"{minutes_to_time(part_start)}-{minutes_to_time(part_end)}")
            return time_intervals
        except:
            return [time_range] * num_parts

    def time_to_minutes(time_str):
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except:
            return 0

    def minutes_to_time(minutes):
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    # Находим индекс последнего урока с занятиями для каждого дня
    for row in soup.select("tbody tr"):
        day_cell = row.find("th")
        if not day_cell:
            continue

        day_text = day_cell.get_text(" ", strip=True)
        days_list.append(day_text)
        lessons_for_day = []
        time_index = 0

        # Сначала собираем все ячейки дня
        all_cells = []
        for td in row.find_all("td"):
            colspan = int(td.get('colspan', 1))
            current_time_range = time_headers[time_index] if time_index < len(time_headers) else None

            lesson_divs = td.find_all("div")
            if lesson_divs:
                time_intervals = split_time_interval(current_time_range, len(lesson_divs))
                lessons_in_cell = []
                for i, div in enumerate(lesson_divs):
                    spans = [s.get_text(strip=True) for s in div.find_all("span")]
                    teacher_room_full = spans[1] if len(spans) > 1 else None
                    teacher = None
                    room = None

                    if teacher_room_full:
                        match = re.search(r'\b\d{3}\b', teacher_room_full)
                        if match:
                            room = match.group(0)
                            teacher = teacher_room_full.replace(room, '').strip()
                        else:
                            teacher = teacher_room_full

                    lesson_time = time_intervals[i] if i < len(time_intervals) else current_time_range
                    lesson = {
                        "time": lesson_time,
                        "subject": spans[0] if len(spans) > 0 else None,
                        "teacher": teacher,
                        "room": room,
                        "group": spans[2] if len(spans) > 2 else None
                    }
                    lessons_in_cell.append(lesson)

                all_cells.append({
                    "colspan": colspan,
                    "lessons": lessons_in_cell,
                    "time_range": current_time_range
                })
            else:
                # Пустая ячейка (нет пар)
                all_cells.append({
                    "colspan": colspan,
                    "lessons": [],
                    "time_range": current_time_range
                })

            time_index += colspan

        # Находим индекс последней ячейки с занятиями
        last_lesson_index = -1
        for i, cell in enumerate(all_cells):
            if cell["lessons"]:  # Если в ячейке есть занятия
                last_lesson_index = i

        # Формируем расписание только до последней ячейки с занятиями
        for i, cell in enumerate(all_cells):
            if i > last_lesson_index and last_lesson_index != -1:
                break  # Прекращаем после последней ячейки с занятиями

            if cell["lessons"]:
                lessons_for_day.append(cell["lessons"])
            else:
                # Добавляем пустой урок
                lessons_for_day.append([{
                    "time": cell["time_range"],
                    "subject": None,
                    "teacher": None,
                    "room": None,
                    "group": None
                }])

        if lessons_for_day:
            schedule[day_text] = lessons_for_day

    # ... остальной код для prev_week_id и next_week_id ...

    prev_week_id = None
    next_week_id = None
    current_week_link = soup.find('a', class_='btn-primary')
    if current_week_link:
        prev_link = current_week_link.find_previous_sibling('a')
        if prev_link and 'href' in prev_link.attrs:
            match = re.search(r'WeekId=(\d+)', prev_link['href'])
            if match:
                prev_week_id = int(match.group(1))

        next_link = current_week_link.find_next_sibling('a')
        if next_link and 'href' in next_link.attrs:
            match = re.search(r'WeekId=(\d+)', next_link['href'])
            if match:
                next_week_id = int(match.group(1))

    return schedule, days_list, prev_week_id, next_week_id

#print(json.dumps(get_schedule(14449, get_group_info("11 нмо")[0]), indent=4, sort_keys=True, ensure_ascii=False))