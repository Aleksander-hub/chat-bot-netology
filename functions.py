import json
from datetime import datetime

TASKS_FILE = "tasks.json"

def save_tasks(tasks):
    """Сохраняет задачи в файл tasks.json."""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def load_tasks():
    """
    Загружает задачи из файла tasks.json, автоматически удаляя прошедшие задачи.
    """
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Фильтруем задачи, оставляя только актуальные (сегодня и в будущем)
    actual_tasks = {
        date: task_list for date, task_list in tasks.items() 
        if date >= today_str and task_list
    }

    # Если были изменения (т.е. старые задачи удалены), сохраняем очищенный список
    if len(actual_tasks) != len(tasks):
        save_tasks(actual_tasks)
        print("Обнаружены и удалены устаревшие задачи.")

    return actual_tasks

def add_task(date: str, task: str) -> str:
    """Добавляет задачу и сохраняет в файл."""
    if not date or not task:
        return "Не удалось добавить задачу: не указана дата или текст."
    
    tasks = load_tasks()
    tasks.setdefault(date, []).append(task)
    save_tasks(tasks)
    
    return f"✅ Добавлено: [{date}] — {task}"

def show_tasks(specific_date: str = None) -> str:
    """Формирует строку с задачами для вывода, загружая их из файла."""
    tasks = load_tasks() # Теперь эта функция возвращает только актуальные задачи
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

    # Если дата не указана, показываем все актуальные задачи
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
        return "Актуальных задач нет."

    return "\n\n".join(all_tasks_parts)

def delete_all_tasks() -> str:
    """Очищает все задачи и сохраняет изменения."""
    save_tasks({})
    return "🗑️ Все задачи удалены."

def delete_tasks(date: str, task_number: int = None) -> str:
    """
    Удаляет задачи на указанную дату.
    Если указан task_number, удаляет конкретную задачу.
    Иначе удаляет все задачи на эту дату.
    """
    tasks = load_tasks()

    if date not in tasks:
        return f"На дату {date} задач для удаления не найдено."

    # Удаление конкретной задачи по номеру
    if task_number is not None:
        try:
            # Номер задачи от пользователя (1-based), конвертируем в индекс (0-based)
            task_index = int(task_number) - 1
            if 0 <= task_index < len(tasks[date]):
                removed_task = tasks[date].pop(task_index)
                # Если на дату больше не осталось задач, удаляем и саму дату
                if not tasks[date]:
                    del tasks[date]
                save_tasks(tasks)
                return f"✅ Задача '{removed_task}' на {date} удалена."
            else:
                return f"❌ Ошибка: задачи с номером {task_number} на {date} не существует."
        except (ValueError, TypeError):
            return "❌ Ошибка: неверный номер задачи."
    # Удаление всех задач на дату
    else:
        del tasks[date]
        save_tasks(tasks)
        return f"🗑️ Все задачи на {date} были удалены."