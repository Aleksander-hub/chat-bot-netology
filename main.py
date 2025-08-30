import telebot
import os
from dotenv import load_dotenv
import keyboards as kb
from functions import (
    load_tasks, save_tasks, add_todo,
    get_tasks_string, clear_all_tasks, parse_date
)
# --- Imports for Scheduler ---
import time
import threading
from datetime import datetime, date
import pytz # <-- Новая библиотека

load_dotenv()

# --- Текст помощи и токен ---
HELP = """
Я - ваш личный бот-помощник для управления задачами.

С помощью кнопок ниже вы можете:
- ❓ **Помощь**: Показать это сообщение.
- ➕ **Добавить задачу**: Начать диалог добавления новой задачи.
- 📋 **Показать задачи**: Увидеть все ваши задачи.
- 🗑️ **Удалить все**: Стереть все задачи безвозвратно.

Для перезапуска бота введите команду /start.
"""
token = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(token)

# --- Настройки для уведомлений ---
# ID администратора для отправки уведомлений.
ADMIN_ID = "8137874571"
# Устанавливаем часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')
# Переменная для хранения даты последней отправки уведомления
last_notification_date = None

tasks = load_tasks()

# --- Логика уведомлений и планировщика ---

def check_tasks_and_notify():
    """Проверяет задачи на сегодня и отправляет уведомление."""
    global last_notification_date

    if ADMIN_ID == "YOUR_TELEGRAM_ID":
        print("Внимание: ADMIN_ID не установлен. Уведомления не будут отправляться.")
        return

    # Получаем сегодняшнюю дату в часовом поясе Москвы
    today_moscow = datetime.now(MOSCOW_TZ).date()
    today_str = today_moscow.strftime('%Y-%m-%d')
    
    # Обновляем дату последнего уведомления
    last_notification_date = today_moscow

    current_tasks = load_tasks()
    if today_str in current_tasks and current_tasks[today_str]:
        tasks_today = current_tasks[today_str]
        message = "Доброе утро! ☀️ На сегодня у вас есть задачи:\n\n"
        for i, task in enumerate(tasks_today, 1):
            message += f"{i}. {task}\n"
        
        try:
            bot.send_message(ADMIN_ID, message)
            print(f"Уведомление о задачах на {today_str} отправлено администратору.")
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
    else:
        print(f"На {today_str} нет задач, уведомление не отправлено.")


def run_scheduler():
    """
    Запускает цикл проверки времени.
    Проверяет время раз в час.
    """
    global last_notification_date
    
    while True:
        now_moscow = datetime.now(MOSCOW_TZ)
        today_moscow = now_moscow.date()

        # Проверяем, что час >= 5 и что мы еще не отправляли уведомление сегодня
        if now_moscow.hour >= 5 and today_moscow != last_notification_date:
            print(f"Время {now_moscow.strftime('%H:%M')} по Москве, запускаю проверку задач...")
            check_tasks_and_notify()

        # Ждем один час
        time.sleep(3600)

# --- Обработчики сообщений Telegram ---

def show_main_menu(chat_id, text="Выберите действие:"):
    """Отправляет сообщение с главным меню."""
    bot.send_message(chat_id, text, reply_markup=kb.create_main_menu_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=["start"])
def start_command(message):
    """Обработчик команды /start."""
    if str(message.chat.id) == str(ADMIN_ID):
        welcome_text = "Добро пожаловать, администратор!\n\n" + HELP
    else:
        welcome_text = "Добро пожаловать!\n\n" + HELP
    show_main_menu(message.chat.id, welcome_text)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Главный обработчик всех нажатий на inline-кнопки."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)

    if call.data == "help":
        show_main_menu(chat_id, HELP)
    elif call.data == "add":
        msg = bot.send_message(chat_id, "Введите дату (сегодня, завтра, ДД.ММ, ММ-ДД или ГГГГ-ММ-ДД)")
        bot.register_next_step_handler(msg, process_date_input)
    elif call.data == "show":
        tasks_string = get_tasks_string(tasks)
        bot.send_message(chat_id, tasks_string)
        show_main_menu(chat_id)
    elif call.data == "delete":
        if not tasks:
            bot.send_message(chat_id, "Список задач уже пуст.")
        else:
            clear_all_tasks(tasks)
            save_tasks(tasks)
            bot.send_message(chat_id, "Все задачи удалены.")
        show_main_menu(chat_id)
    elif call.data.startswith("confirm_yes:"):
        proposed_date = call.data.split(":")[1]
        ask_for_task_text(chat_id, proposed_date)
    elif call.data == "confirm_no":
        bot.send_message(chat_id, "Ввод отменен.")
        show_main_menu(chat_id)

def process_date_input(message):
    """Обрабатывает введенную пользователем дату."""
    status, date_str = parse_date(message.text)
    if status == "ok":
        ask_for_task_text(message.chat.id, date_str)
    elif status == "past":
        bot.send_message(
            message.chat.id,
            f"Эта дата в прошлом. Вы имели в виду {date_str}?",
            reply_markup=kb.create_yes_no_keyboard(date_str)
        )
    elif status == "invalid":
        error_text = "Неверный формат даты. Попробуйте еще раз."
        if date_str == "past_date":
             error_text = "Вы указали уже прошедшую дату."
        bot.send_message(message.chat.id, error_text)
        show_main_menu(message.chat.id)

def ask_for_task_text(chat_id, date_str):
    """Запрашивает у пользователя текст задачи."""
    msg = bot.send_message(chat_id, "Теперь введите текст задачи:")
    bot.register_next_step_handler(msg, process_task, date_str)

def process_task(message, date):
    """Обрабатывает текст задачи и сохраняет ее."""
    task = message.text.strip()
    add_todo(date, task, tasks)
    save_tasks(tasks)
    bot.send_message(message.chat.id, f"✅ Добавлено: [{date}] — {task}")
    show_main_menu(message.chat.id)

@bot.message_handler(content_types=["text"])
def echo(message):
    show_main_menu(message.chat.id, "Используйте кнопки для навигации.")

# --- Запуск бота и планировщика ---
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Планировщик запущен в фоновом режиме (проверка раз в час).")
    
    print("Бот запускается...")
    bot.polling(none_stop=True)

