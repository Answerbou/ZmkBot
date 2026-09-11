        import os
import logging
import threading
from datetime import datetime, timedelta
import requests
from flask import Flask, Response, abort
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8881616068:AAEQJCDcWMT658KbX-1RIWqWz7gg4GXJhs8"  # ТОКЕН ОТ @BotFather
BASE_URL = "https://www.zelmex.ru/images/stories/"
# Публичный адрес Railway (получишь после первого деплоя, см. ниже)
PUBLIC_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "https://your-app.up.railway.app")
if not PUBLIC_URL.startswith("http"):
    PUBLIC_URL = "https://" + PUBLIC_URL

# --- FLASK: САЙТ-ПРОКСИ ---
app = Flask(__name__)

@app.route("/")
def index():
    return "ZMK Bot is running"

@app.route("/pdf/<ddmm>")
def serve_pdf(ddmm):
    """Скачивает PDF с zelmex.ru и отдаёт его браузеру."""
    url = BASE_URL + ddmm + ".pdf"
    try:
        headers = {"Referer": "https://www.zelmex.ru/index.php/raspisanie"}
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            return Response(
                r.content,
                mimetype="application/pdf",
                headers={"Content-Disposition": f"inline; filename=raspisanie_{ddmm}.pdf"}
            )
    except Exception as e:
        logging.error(f"Ошибка скачивания PDF {url}: {e}")
    abort(404)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- БАЗА ПРЕПОДАВАТЕЛЕЙ ---
TEACHERS = {
    # ... твой словарь TEACHERS (оставь как было) ...
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ФУНКЦИИ БОТА ---

def get_pdf_url(date):
    ddmm = date.strftime("%d%m")
    return f"{PUBLIC_URL}/pdf/{ddmm}"

def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📅 Расписание", callback_data="menu_schedule")],
        [InlineKeyboardButton("👨‍🏫 Учителя ЗМК", callback_data="menu_teachers")],
    ]
    update.message.reply_text("Привет! Я бот ЗМК.\nВыбери, что тебе нужно:", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "menu_schedule":
        keyboard = [
            [InlineKeyboardButton("Сегодня", callback_data="sched_today"),
             InlineKeyboardButton("Завтра", callback_data="sched_tomorrow")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="menu_main")],
        ]
        query.edit_message_text("Выбери день:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "sched_today":
        show_schedule(query, datetime.now())

    elif data == "sched_tomorrow":
        show_schedule(query, datetime.now() + timedelta(days=1))

    elif data == "menu_teachers":
        keys = list(TEACHERS.keys())
        buttons = []
        for i in range(0, len(keys), 2):
            row = [InlineKeyboardButton(TEACHERS[keys[i]]["name"], callback_data=f"teacher_{keys[i]}")]
            if i + 1 < len(keys):
                row.append(InlineKeyboardButton(TEACHERS[keys[i+1]]["name"], callback_data=f"teacher_{keys[i+1]}"))
            buttons.append(row)
        buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu_main")])
        query.edit_message_text("Список преподавателей:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("teacher_"):
        key = data.replace("teacher_", "")
        t = TEACHERS.get(key)
        if t:
            text = f"👤 *{t['name']}*\n\n📚 Предмет: {t['subject']}\n\nℹ️ {t['info']}"
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="menu_teachers")]]
            query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_main":
        start(update, context)

def show_schedule(query, date):
    """Отправляет ссылку на PDF через сайт-прокси."""
    url = get_pdf_url(date)
    text = (
        f"📅 Расписание на {date.strftime('%d.%m.%Y')}:\n\n"
        f"🔗 [Открыть PDF]({url})\n\n"
        f"_Если ссылка не открывается — значит, на эту дату файла нет._"
    )
    query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=False)

# --- ЗАПУСК ---

def main():
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Запускаем бота
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    print("Бот и веб-сервер запущены.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
