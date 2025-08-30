import json
from datetime import datetime, timedelta
import re

TASKS_FILE = "tasks.json"

def parse_date(user_input):
    """
    Парсит ввод пользователя и возвращает дату.
    Возвращает кортеж (статус, дата).
    Статусы: "ok", "past", "invalid".
    """
    user_input = user_input.strip().lower()
    today = datetime.now().date()

    if user_input == "сегодня":
        return "ok", today.strftime('%Y-%m-%d')
    elif user_input == "завтра":
        tomorrow = today + timedelta(days=1)
        return "ok", tomorrow.strftime('%Y-%m-%d')

    # Проверка на ДД.ММ
    match = re.fullmatch(r'(\d{2})\.(\d{2})', user_input)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        try:
            date = datetime(today.year, month, day).date()
            if date < today:
                return "past", date.replace(year=today.year + 1).strftime('%Y-%m-%d')
            else:
                return "ok", date.strftime('%Y-%m-%d')
        except ValueError:
            return "invalid", None

    # Проверка на ММ-ДД
    match = re.fullmatch(r'(\d{2})-(\d{2})', user_input)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        try:
            date = datetime(today.year, month, day).date()
            if date < today:
                return "past", date.replace(year=today.year + 1).strftime('%Y-%m-%d')
            else:
                return "ok", date.strftime('%Y-%m-%d')
        except ValueError:
            return "invalid", None

    # Проверка на ГГГГ-ММ-ДД
    match = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', user_input)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            date = datetime(year, month, day).date()
            if date < today:
                return "invalid", "past_date"
            return "ok", date.strftime('%Y-%m-%d')
        except ValueError:
            return "invalid", None
            
    return "invalid", None

def load_tasks():
    """Загружает задачи из файла tasks.json."""
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_tasks(tasks):
    """Сохраняет задачи в файл tasks.json."""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def add_todo(date, task, tasks):
    """Добавляет задачу в словарь (модифицирует на месте)."""
    tasks.setdefault(date, []).append(task)

def get_tasks_string(tasks):
    """Формирует строку с задачами для вывода."""
    if not tasks:
        return "Список задач пуст"
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    today_tasks_formatted = []
    other_tasks_formatted = []

    for date, task_list in sorted(tasks.items()):
        if not task_list:
            continue
        
        # Форматируем задачи для одной даты
        formatted_tasks = []
        for i, t in enumerate(task_list, 1):
            formatted_tasks.append(f"  {i}. {t}")
        
        # Распределяем
        if date == today_str:
            today_tasks_formatted.extend(formatted_tasks)
        else:
            other_tasks_formatted.append(f"{date}:\n" + "\n".join(formatted_tasks))

    # Собираем итоговое сообщение
    final_message_parts = []
    if today_tasks_formatted:
        final_message_parts.append("--- Задачи на сегодня ---")
        final_message_parts.append("\n".join(today_tasks_formatted))

    if other_tasks_formatted:
        final_message_parts.append("\n".join(other_tasks_formatted))
        
    return "\n\n".join(final_message_parts) if final_message_parts else "Список задач пуст"

def clear_all_tasks(tasks):
    """Очищает все задачи (модифицирует на месте)."""
    tasks.clear()
