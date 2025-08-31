import json
from datetime import datetime

TASKS_FILE = "tasks.json"

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

def get_tasks_string(tasks, specific_date=None):
    """Формирует строку с задачами для вывода.

    Args:
        tasks (dict): Словарь с задачами.
        specific_date (str, optional): Если указана, показывает задачи только на эту дату.
    """
    if not tasks:
        return "Список задач пуст."

    # Если запрошена конкретная дата
    if specific_date:
        if specific_date in tasks and tasks[specific_date]:
            task_list = tasks[specific_date]
            formatted_tasks = [f"{i}. {t}" for i, t in enumerate(task_list, 1)]
            return f"Задачи на {specific_date}:\n" + "\n".join(formatted_tasks)
        else:
            return f"На {specific_date} задач нет."

    # Если дата не указана, показываем все задачи
    all_tasks_parts = []
    today_str = datetime.now().strftime('%Y-%m-%d')

    # Сначала задачи на сегодня, если они есть
    if today_str in tasks and tasks[today_str]:
        all_tasks_parts.append("--- Задачи на сегодня ---")
        today_tasks = [f"  {i}. {t}" for i, t in enumerate(tasks[today_str], 1)]
        all_tasks_parts.append("\n".join(today_tasks))

    # Затем остальные задачи, отсортированные по дате
    other_tasks_parts = []
    for date, task_list in sorted(tasks.items()):
        if date == today_str or not task_list:
            continue
        formatted_tasks = [f"  {i}. {t}" for i, t in enumerate(task_list, 1)]
        other_tasks_parts.append(f"{date}:\n" + "\n".join(formatted_tasks))
    
    if other_tasks_parts:
        all_tasks_parts.append("--- Остальные задачи ---")
        all_tasks_parts.append("\n\n".join(other_tasks_parts))

    if not all_tasks_parts:
        return "Список задач пуст."

    return "\n\n".join(all_tasks_parts)

def clear_all_tasks(tasks):
    """Очищает все задачи (модифицирует на месте)."""
    tasks.clear()