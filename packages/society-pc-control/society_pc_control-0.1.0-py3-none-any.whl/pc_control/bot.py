import telebot
from telebot import types
import threading
import time
import os
from .config import BOT_TOKEN, MOUSE_MOVE_STEP, MOUSE_MOVE_ACCELERATED
from .utils import load_json_file, save_json_file, generate_token
from .control import take_screenshot, type_text_smart, press_hotkey, move_mouse, click_mouse, scroll_mouse

bot = telebot.TeleBot(BOT_TOKEN)

users = load_json_file("users_db.json")
access_tokens = load_json_file("access_tokens.json")

def save_all():
    save_json_file("users_db.json", users)
    save_json_file("access_tokens.json", access_tokens)

def get_user_status(user_id):
    user_id = str(user_id)
    return users.get(user_id, {}).get("status", 0)

def set_user_status(user_id, status):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {"status": status}
    else:
        users[user_id]["status"] = status
    save_all()

def generate_access_token(user_id):
    token = generate_token()
    access_tokens[str(user_id)] = {"token": token, "created_at": time.time()}
    save_all()
    return token

def check_access(user_id):
    user_id = str(user_id)
    token_info = access_tokens.get(user_id)
    if not token_info:
        return False
    if time.time() - token_info.get("created_at", 0) > 600:
        del access_tokens[user_id]
        save_all()
        return False
    return True

# --- Управление режимами ---

user_modes = {}  # user_id -> mode ('mouse', 'keyboard', 'hotkeys', None)

def main_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🖱 Мышь", callback_data="mode_mouse"),
        types.InlineKeyboardButton("⌨ Клавиатура", callback_data="mode_keyboard"),
        types.InlineKeyboardButton("⚡ Горячие клавиши", callback_data="mode_hotkeys"),
        types.InlineKeyboardButton("📸 Скриншот", callback_data="screenshot")
    )
    return keyboard

def mouse_control_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        types.InlineKeyboardButton("⬆️", callback_data="mouse_up"),
    )
    keyboard.add(
        types.InlineKeyboardButton("⬅️", callback_data="mouse_left"),
        types.InlineKeyboardButton("⬇️", callback_data="mouse_down"),
        types.InlineKeyboardButton("➡️", callback_data="mouse_right"),
    )
    keyboard.add(
        types.InlineKeyboardButton("Левый клик 🖱", callback_data="click_left"),
        types.InlineKeyboardButton("Правый клик 🖱", callback_data="click_right"),
        types.InlineKeyboardButton("Двойной клик 🖱", callback_data="click_double"),
    )
    keyboard.add(
        types.InlineKeyboardButton("Прокрутить вверх 🔼", callback_data="scroll_up"),
        types.InlineKeyboardButton("Прокрутить вниз 🔽", callback_data="scroll_down"),
    )
    keyboard.add(
        types.InlineKeyboardButton("⬅ Главное меню", callback_data="main_menu")
    )
    return keyboard

def keyboard_control_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("Ввести текст", callback_data="enter_text"),
        types.InlineKeyboardButton("Назад ⬅", callback_data="main_menu")
    )
    return keyboard

def hotkeys_keyboard():
    # Пример горячих клавиш
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        types.InlineKeyboardButton("Ctrl+C", callback_data="hotkey_ctrl_c"),
        types.InlineKeyboardButton("Ctrl+V", callback_data="hotkey_ctrl_v"),
        types.InlineKeyboardButton("Alt+Tab", callback_data="hotkey_alt_tab"),
    )
    keyboard.add(
        types.InlineKeyboardButton("Назад ⬅", callback_data="main_menu")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        status = 2 if not users else 0
        users[user_id] = {"status": status}
        save_all()
    status = get_user_status(user_id)
    greetings = {
        0: "👋 Привет! У тебя нет доступа. Обратись к администратору.",
        1: "🎉 Добро пожаловать! Используй главное меню.",
        2: "🛠 Привет, админ! Используй главное меню."
    }
    bot.send_message(message.chat.id, greetings.get(status, "Привет!"), reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = str(call.from_user.id)
    status = get_user_status(user_id)
    if status == 0:
        bot.answer_callback_query(call.id, "⛔ Нет доступа!")
        return
    if not check_access(user_id):
        bot.answer_callback_query(call.id, "⛔ Токен доступа истёк. Введите /pc для нового токена.")
        return

    data = call.data

    if data == "main_menu":
        user_modes[user_id] = None
        bot.edit_message_text("Главное меню:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

    elif data == "mode_mouse":
        user_modes[user_id] = "mouse"
        bot.edit_message_text("Управление мышью:", call.message.chat.id, call.message.message_id, reply_markup=mouse_control_keyboard())

    elif data.startswith("mouse_") and user_modes.get(user_id) == "mouse":
        step = MOUSE_MOVE_ACCELERATED if "shift" in data else MOUSE_MOVE_STEP
        if data == "mouse_up":
            move_mouse(0, -1, accelerated=False)
        elif data == "mouse_down":
            move_mouse(0, 1, accelerated=False)
        elif data == "mouse_left":
            move_mouse(-1, 0, accelerated=False)
        elif data == "mouse_right":
            move_mouse(1, 0, accelerated=False)
        bot.answer_callback_query(call.id, "Мышь сдвинута")
        # Не меняем текст, чтобы не дергался интерфейс

    elif data.startswith("click_") and user_modes.get(user_id) == "mouse":
        if data == "click_left":
            click_mouse('left')
        elif data == "click_right":
            click_mouse('right')
        elif data == "click_double":
            click_mouse('left')
            click_mouse('left')
        bot.answer_callback_query(call.id, "Клик выполнен")

    elif data == "scroll_up" and user_modes.get(user_id) == "mouse":
        scroll_mouse(100)
        bot.answer_callback_query(call.id, "Прокрутка вверх")

    elif data == "scroll_down" and user_modes.get(user_id) == "mouse":
        scroll_mouse(-100)
        bot.answer_callback_query(call.id, "Прокрутка вниз")

    elif data == "mode_keyboard":
        user_modes[user_id] = "keyboard"
        bot.edit_message_text("Управление клавиатурой.\nНажмите кнопку ниже, чтобы ввести текст.", call.message.chat.id, call.message.message_id, reply_markup=keyboard_control_keyboard())

    elif data == "enter_text":
        bot.answer_callback_query(call.id, "Напишите текст в чат. Он будет введён на ПК.")
        user_modes[user_id] = "text_input"

    elif user_modes.get(user_id) == "text_input":
        # Этот блок вызывается на новое сообщение ниже

        pass

    elif data == "mode_hotkeys":
        user_modes[user_id] = "hotkeys"
        bot.edit_message_text("Горячие клавиши:", call.message.chat.id, call.message.message_id, reply_markup=hotkeys_keyboard())

    elif data.startswith("hotkey_") and user_modes.get(user_id) == "hotkeys":
        mapping = {
            "hotkey_ctrl_c": ("ctrl", "c"),
            "hotkey_ctrl_v": ("ctrl", "v"),
            "hotkey_alt_tab": ("alt", "tab"),
        }
        keys = mapping.get(data)
        if keys:
            press_hotkey(*keys)
            bot.answer_callback_query(call.id, f"Горячая клавиша { '+'.join(keys).upper() } выполнена")

@bot.message_handler(func=lambda m: True)
def message_handler(message):
    user_id = str(message.from_user.id)
    status = get_user_status(user_id)

    if status == 0:
        bot.reply_to(message, "⛔ У вас нет доступа.")
        return

    if not check_access(user_id):
        bot.reply_to(message, "⛔ Токен доступа истёк. Используйте /pc для нового токена.")
        return

    mode = user_modes.get(user_id)
    if mode == "text_input":
        type_text_smart(message.text)
        bot.send_message(message.chat.id, f"✅ Текст введён: {message.text}")
        user_modes[user_id] = "keyboard"
    else:
        bot.send_message(message.chat.id, "ℹ️ Используйте меню для управления компьютером.", reply_markup=main_menu())

@bot.message_handler(commands=['pc'])
def request_pc_access(message):
    user_id = str(message.from_user.id)
    if get_user_status(user_id) == 0:
        bot.reply_to(message, "⛔ У вас нет доступа.")
        return
    token = generate_access_token(user_id)
    bot.send_message(message.chat.id, f"🔑 Ваш токен доступа (действует 10 мин):\n<code>{token}</code>", parse_mode='HTML')

@bot.message_handler(commands=['start', 'admin', 'set_status', 'guide'])
def admin_and_others(message):
    # Реализовать как в основном примере, или вынести в отдельные хендлеры
    pass

def run_bot():
    print("[BOT] Запуск...")
    bot.infinity_polling()

class PCControlModule:
    def __init__(self):
        threading.Thread(target=run_bot, daemon=True).start()
        print("[PCControlModule] Telegram бот запущен в фоне.")

if __name__ == '__main__':
    run_bot()
