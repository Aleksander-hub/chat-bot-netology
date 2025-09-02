import json
from datetime import date, timedelta
import functions
import openrouter_ai

# Глобальная переменная для хранения состояния диалога
# Формат: {user_id: {'state': 'some_state', 'params': {...}}}
conversation_state = {}

def load_prompt() -> str:
    """Загружает системный промпт из файла."""
    with open('ai_prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    prompt = prompt.replace('{current_date}', today.strftime('%Y-%m-%d'))
    prompt = prompt.replace('{current_date_tomorrow}', tomorrow.strftime('%Y-%m-%d'))
    prompt = prompt.replace('{day_after_tomorrow_date}', day_after_tomorrow.strftime('%Y-%m-%d'))
    
    return prompt

def process_message(user_id: int, text: str) -> str:
    """
    Обрабатывает сообщение пользователя, определяет намерение и возвращает ответ.
    """
    global conversation_state

    state_info = conversation_state.get(user_id)

    # 1. Проверка, ожидаем ли мы подтверждения какого-либо действия
    if state_info:
        state = state_info.get('state')
        # Подтверждение удаления ВСЕХ задач
        if state == 'awaiting_confirmation_delete_all':
            if text.lower() in ['да', 'yes']:
                conversation_state.pop(user_id, None)
                return functions.delete_all_tasks()
            elif text.lower() in ['нет', 'no']:
                conversation_state.pop(user_id, None)
                return "Отмена операции. Задачи не были удалены."
            else:
                return "Пожалуйста, ответьте 'да' или 'нет'."
        
        # Подтверждение удаления конкретных задач (по дате или номеру)
        elif state == 'awaiting_confirmation_delete_specific':
            if text.lower() in ['да', 'yes']:
                params = state_info.get('params', {})
                result = functions.delete_tasks(date=params.get('date'), task_number=params.get('task_number'))
                conversation_state.pop(user_id, None)
                return result
            elif text.lower() in ['нет', 'no']:
                conversation_state.pop(user_id, None)
                return "Отмена операции. Ничего не было удалено."
            else:
                return "Пожалуйста, ответьте 'да' или 'нет'."

    # 2. Основная логика, если нет активного состояния
    prompt = load_prompt()
    ai_response_text = openrouter_ai.get_ai_response(prompt, text)

    try:
        tool_call = json.loads(ai_response_text)
        if 'tool_call' in tool_call:
            command = tool_call['tool_call']
            args = tool_call.get('arguments', {})

            if command == 'add_task':
                return functions.add_task(args.get('date'), args.get('task'))
            
            elif command == 'show_tasks':
                return functions.show_tasks(args.get('date'))
            
            elif command == 'delete_tasks':
                params = {'date': args.get('date'), 'task_number': args.get('task_number')}
                if not params['date']:
                    return "Не могу удалить, т.к. не понял дату. Попробуйте уточнить."
                
                if params['task_number'] is not None:
                    confirmation_question = f"Вы уверены, что хотите удалить задачу №{params['task_number']} на {params['date']}? (да/нет)"
                else:
                    confirmation_question = f"Вы уверены, что хотите удалить ВСЕ задачи на {params['date']}? (да/нет)"
                
                conversation_state[user_id] = {
                    'state': 'awaiting_confirmation_delete_specific',
                    'params': params
                }
                return confirmation_question

            elif command == 'delete_all_tasks':
                conversation_state[user_id] = {'state': 'awaiting_confirmation_delete_all', 'params': {}}
                return "Вы уверены, что хотите удалить АБСОЛЮТНО все задачи? Это действие необратимо. (да/нет)"
            
            else:
                return f"Неизвестная команда от AI: {command}"

    except (json.JSONDecodeError, TypeError):
        return ai_response_text

    return "Что-то пошло не так при обработке вашего запроса."