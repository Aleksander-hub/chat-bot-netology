import telebot
import os
import json
from dotenv import load_dotenv
from pydub import AudioSegment

# --- Кастомные импорты ---
import keyboards as kb
import gemini_ai as ai
from functions import (
    load_tasks, save_tasks, add_todo,
    get_tasks_string, clear_all_tasks
)

# --- Импорты для планировщика ---
import time
import threading
from datetime import datetime
import pytz

# --- Инициализация ---
load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(token)
tasks = load_tasks()

# --- Константы и настройки ---
HELP = """
Я - ваш личный AI-ассистент для управления задачами. 

**Что я умею:**
- Добавлять задачи голосом или текстом (например, *"добавь на завтра купить молоко"*).
- Показывать задачи (*"что у меня на сегодня?"*).
- Удалять все задачи.
- Помогать (*"помощь"* или *"что ты умеешь"*).

Вы также можете использовать кнопки в меню.
Для перезапуска введите команду /start.
"""
ADMIN_ID = "8137874571"  # ID администратора для уведомлений
MOSCOW_TZ = pytz.timezone('Europe/Moscow')
last_notification_date = None
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- Основная логика обработки команд ---
def process_command(text, chat_id):
    """Центральная функция для обработки текстовых команд, полученных от пользователя или после распознавания голоса."""
    bot.send_message(chat_id, "Думаю... 🤔", disable_notification=True)
    
    # Получаем намерение от AI
    intent_json_str = ai.get_intent(text)
    print(f"[AI] Распознано намерение: {intent_json_str}")

    try:
        intent_data = json.loads(intent_json_str)
        intent = intent_data.get("intent", "unknown")

        if intent == "add_task":
            date = intent_data.get("date")
            task = intent_data.get("task")
            if date and task:
                add_todo(date, task, tasks)
                save_tasks(tasks)
                bot.send_message(chat_id, f"✅ Добавлено: [{date}] — {task}")
            else:
                bot.send_message(chat_id, "Не смог распознать дату или текст задачи. Попробуйте еще раз.")
            show_main_menu(chat_id)

        elif intent == "show_tasks":
            tasks_string = get_tasks_string(tasks, intent_data.get("date"))
            bot.send_message(chat_id, tasks_string)
            show_main_menu(chat_id)

        elif intent == "delete_tasks":
            # Пока что удаляем все, в будущем можно расширить на конкретную дату
            clear_all_tasks(tasks)
            save_tasks(tasks)
            bot.send_message(chat_id, "🗑️ Все задачи удалены.")
            show_main_menu(chat_id)

        elif intent == "help":
            show_main_menu(chat_id, HELP)

        else: # unknown intent
            bot.send_message(chat_id, "Не совсем понял вас. Попробуйте переформулировать или воспользуйтесь кнопками.")
            show_main_menu(chat_id)

    except json.JSONDecodeError:
        print(f"[Ошибка] Не удалось распарсить JSON от AI: {intent_json_str}")
        bot.send_message(chat_id, "Произошла внутренняя ошибка при обработке вашего запроса. Попробуйте позже.")
        show_main_menu(chat_id)

# --- Обработчики сообщений Telegram ---
@bot.message_handler(commands=["start"])
def start_command(message):
    """Обработчик команды /start."""
    welcome_text = f"Добро пожаловать, {message.from_user.first_name}!" + HELP
    show_main_menu(message.chat.id, welcome_text)

@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    """Обрабатывает голосовые сообщения."""
    chat_id = message.chat.id
    try:
        bot.send_message(chat_id, "Получил голосовое, распознаю... 🎤", disable_notification=True)
        
        # Скачиваем oga файл
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        oga_path = os.path.join(TEMP_DIR, f"{message.voice.file_id}.oga")
        with open(oga_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Конвертируем в wav
        wav_path = os.path.join(TEMP_DIR, f"{message.voice.file_id}.wav")
        audio = AudioSegment.from_ogg(oga_path)
        audio.export(wav_path, format="wav")
        print(f"[Аудио] Конвертировано в {wav_path}")

        # Распознаем речь
        recognized_text = ai.speech_to_text(wav_path)

        # Очистка временных файлов
        os.remove(oga_path)
        os.remove(wav_path)

        if recognized_text:
            bot.send_message(chat_id, f"Вы сказали: *{recognized_text}*", parse_mode='Markdown')
            process_command(recognized_text, chat_id)
        else:
            bot.send_message(chat_id, "Не удалось распознать речь. Попробуйте еще раз.")
            show_main_menu(chat_id)

    except Exception as e:
        print(f"[Ошибка] Проблема с обработкой голоса: {e}")
        bot.send_message(chat_id, "Произошла ошибка при обработке вашего голосового сообщения.")
        show_main_menu(chat_id)

@bot.message_handler(content_types=["text"])
def handle_text_message(message):
    """Обрабатывает текстовые сообщения, прогоняя их через AI."""
    process_command(message.text, message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Обработчик нажатий на inline-кнопки."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None) # Убираем кнопки

    command = call.data
    
    # Для простых команд можно не использовать AI, а действовать напрямую
    if command == "help":
        show_main_menu(chat_id, HELP)
    elif command == "show":
        tasks_string = get_tasks_string(tasks)
        bot.send_message(chat_id, tasks_string)
        show_main_menu(chat_id)
    elif command == "delete":
        clear_all_tasks(tasks)
        save_tasks(tasks)
        bot.send_message(chat_id, "🗑️ Все задачи удалены.")
        show_main_menu(chat_id)
    elif command == "add":
        # Для добавления задачи нужен диалог, который AI пока не умеет вести
        msg = bot.send_message(chat_id, "Введите задачу и дату (например, 'купить молоко завтра'):")
        bot.register_next_step_handler(msg, lambda m: process_command(m.text, m.chat.id))

def show_main_menu(chat_id, text="Выберите действие или дайте команду голосом/текстом:"):
    """Отправляет сообщение с главным меню."""
    bot.send_message(chat_id, text, reply_markup=kb.create_main_menu_keyboard(), parse_mode='Markdown')

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
        if now_moscow.hour >= 9:
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