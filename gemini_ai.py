import google.generativeai as genai
import os
from pydub import AudioSegment
from datetime import datetime, timedelta

# Загрузка ключа API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# --- Модели ---
# Модель для распознавания речи (аудио)
speech_to_text_model = genai.GenerativeModel('models/gemini-1.5-flash')

# Модель для распознавания намерений (текст)
get_intent_model = genai.GenerativeModel('models/gemini-1.5-pro')


def speech_to_text(audio_file_path):
    """
    Преобразует аудиофайл в текст с помощью Gemini API.
    Возвращает распознанный текст или None в случае ошибки.
    """
    try:
        # Загружаем аудиофайл
        audio_file = genai.upload_file(path=audio_file_path)
        print(f"Файл {audio_file.name} успешно загружен на сервер Gemini.")

        # Отправляем запрос на распознавание
        response = speech_to_text_model.generate_content(
            ["Распознай этот аудиофайл", audio_file],
            stream=False
        )

        # Освобождаем ресурсы
        genai.delete_file(audio_file.name)
        print(f"Файл {audio_file.name} удален с сервера Gemini.")

        return response.text.strip()
    except Exception as e:
        print(f"Ошибка при распознавании речи: {e}")
        # Если файл был загружен, но произошла другая ошибка, пытаемся его удалить
        if 'audio_file' in locals() and audio_file:
            try:
                genai.delete_file(audio_file.name)
                print(f"Файл {audio_file.name} удален с сервера Gemini после ошибки.")
            except Exception as delete_e:
                print(f"Не удалось удалить файл {audio_file.name} после ошибки: {delete_e}")
        return None

def get_intent(text):
    """
    Анализирует текст и возвращает намерение в формате JSON.
    """
    try:
        # Загружаем промпт-инструкцию из файла
        with open('ai_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # Динамически подставляем текущие даты в промпт
        today = datetime.now().date()
        prompt = prompt_template.format(
            current_date=today.strftime('%Y-%m-%d'),
            tomorrow_date=(today + timedelta(days=1)).strftime('%Y-%m-%d'),
            day_after_tomorrow_date=(today + timedelta(days=2)).strftime('%Y-%m-%d')
        )

        # Отправляем запрос в модель
        response = get_intent_model.generate_content(prompt + "\n\nТекст пользователя: " + text)
        
        # Возвращаем "сырой" ответ модели для дальнейшей обработки
        return response.text

    except Exception as e:
        print(f"Ошибка при определении намерения: {e}")
        return '{"intent": "unknown", "error": "internal_error"}'
