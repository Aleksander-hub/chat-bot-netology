from openai import OpenAI
import os

def get_client():
    """Возвращает инициализированный клиент OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Не найден OPENROUTER_API_KEY в .env файле!")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def get_ai_response(system_prompt: str, user_text: str) -> str:
    """
    Отправляет запрос к модели OpenRouter с заданным системным промптом и текстом пользователя.
    Возвращает "сырой" ответ от модели (может быть JSON или обычный текст).
    """
    try:
        client = get_client()
        
        completion = client.chat.completions.create(
            model="qwen/qwen-turbo", # Using a faster model
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_text,
                },
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost", # Replace with your site URL
                "X-Title": "Chat Bot Netology", # Replace with your app name
            }
        )

        result = completion.choices[0].message.content or ""
        return result.strip()

    except Exception as e:
        print(f"Ошибка при вызове модели OpenRouter: {e}")
        # Возвращаем пустую строку или информацию об ошибке, чтобы ai_core мог ее обработать
        return "Произошла ошибка при обращении к AI. Пожалуйста, попробуйте позже."

# Функции get_intent, chat_reply, speech_to_text, _extract_json_object удалены как устаревшие.