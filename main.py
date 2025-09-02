import telebot
import os
from dotenv import load_dotenv

# --- Кастомные импорты ---
import ai_core  # Наше новое AI-ядро

# --- Импорты для планировщика (остаются без изменений) ---
import time
import threading
from datetime import datetime
import pytz
from functions import load_tasks # Планировщику все еще нужно загружать задачи

# --- Инициализация ---
load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
if not token:
    raise ValueError("Не найден TELEGRAM_TOKEN в .env файле!")
bot = telebot.TeleBot(token)

# --- Константы и настройки для планировщика ---
ADMIN_ID = os.getenv('ADMIN_ID', "YOUR_TELEGRAM_ID")
MOSCOW_TZ = pytz.timezone('Europe/Moscow')
last_notification_date = None

# --- Справка ---
try:
    with open('help.txt', 'r', encoding='utf-8') as f:
        HELP_MESSAGE = f.read()
except FileNotFoundError:
    HELP_MESSAGE = "Не удалось загрузить справку. Обратитесь к администратору."

# --- Обработчики сообщений Telegram ---

@bot.message_handler(commands=["start", "help"])
def start_help_command(message):
    """Обработчик команд /start и /help."""
    bot.send_message(message.chat.id, HELP_MESSAGE, parse_mode='Markdown')

@bot.message_handler(content_types=["text"])
def handle_text_message(message):
    """
    Основной обработчик текстовых сообщений.
    Передает текст в AI-ядро и отправляет ответ пользователю.
    """
    user_id = message.chat.id
    text = message.text

    # Отправляем "Думаю..." для обратной связи
    thinking_message = bot.send_message(user_id, "Думаю... 🤔", disable_notification=True)

    try:
        # Получаем ответ от AI-ядра
        response = ai_core.process_message(user_id, text)
        bot.edit_message_text(response, user_id, thinking_message.message_id)
    except Exception as e:
        print(f"[Ошибка] Проблема в AI-ядре: {e}")
        bot.edit_message_text("Произошла внутренняя ошибка. Попробуйте позже.", user_id, thinking_message.message_id)


# --- Логика уведомлений и планировщика (без изменений) ---
def check_tasks_and_notify():
    """Проверяет задачи на сегодня и отправляет уведомление."""
    global last_notification_date
    if ADMIN_ID == "YOUR_TELEGRAM_ID":
        print("Внимание: ADMIN_ID не установлен. Уведомления не будут отправляться.")
        return

    today_moscow = datetime.now(MOSCOW_TZ).date()
    today_str = today_moscow.strftime('%Y-%m-%d')

    if today_moscow == last_notification_date:
        return # Уже отправляли сегодня

    current_tasks = load_tasks()
    if today_str in current_tasks and current_tasks[today_str]:
        tasks_today = current_tasks[today_str]
        message = "Доброе утро! ☀️ На сегодня у вас есть задачи:\n\n"
        for i, task in enumerate(tasks_today, 1):
            message += f"{i}. {task}\n"

        try:
            bot.send_message(ADMIN_ID, message)
            last_notification_date = today_moscow # Обновляем дату после успешной отправки
            print(f"Уведомление о задачах на {today_str} отправлено.")
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
    else:
        print(f"На {today_str} нет задач, уведомление не отправлено.")

def run_scheduler():
    """Запускает цикл проверки времени для уведомлений."""
    while True:
        now_moscow = datetime.now(MOSCOW_TZ)
        # Проверяем задачи в определенное время, например, в 9 утра
        if now_moscow.hour == 9:
            check_tasks_and_notify()
        time.sleep(3600) # Проверка раз в час

# --- Запуск бота и планировщика ---
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Планировщик запущен.")

    print("AI-бот запускается...")
    bot.polling(none_stop=True)