from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_main_menu_keyboard():
    """Создает клавиатуру главного меню."""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    markup.row(InlineKeyboardButton("➕ Добавить задачу", callback_data="add"))
    markup.row(InlineKeyboardButton("📋 Показать задачи", callback_data="show"))
    markup.row(InlineKeyboardButton("🗑️ Удалить все", callback_data="delete"))
    return markup

def create_yes_no_keyboard(date_str):
    """Создает клавиатуру с кнопками 'Да' и 'Нет' для подтверждения даты."""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Да", callback_data=f"confirm_yes:{date_str}"),
        InlineKeyboardButton("Нет", callback_data="confirm_no")
    )
    return markup
