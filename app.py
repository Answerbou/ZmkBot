import os
import logging
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from flask import Flask, Response, abort
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# --- ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Публичный адрес сервиса на FPS.ms (получишь после первого запуска)
PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://your-app.fps.ms")
BASE_URL = "https://www.zelmex.ru/images/stories/"

# --- FLASK: САЙТ-ПРОКСИ ДЛЯ PDF ---
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

# --- БАЗА ПРЕПОДАВАТЕЛЕЙ ЗМК ---
TEACHERS = {
    "muhanov": {"name": "Муханов Виктор Семенович", "subject": "Директор колледжа", "info": "Народный учитель РТ. Руководит ЗМК, тесно сотрудничает с ПОЗиС.", "photo": None},
    "belov": {"name": "Белов Михаил Вячеславович", "subject": "Мехатроника и мобильная робототехника", "info": "Победитель регионального этапа 'Мастер года' (2026). Работает с роботами-манипуляторами и лазерным станком.", "photo": None},
    "kuzmina": {"name": "Кузьмина Маргарита Радиевна", "subject": "Физика", "info": "Первая категория, 9 лет стажа. Победитель конкурса 'Лучший молодой преподаватель'. Благодарности за олимпиады.", "photo": None},
    "komyagina": {"name": "Комягина Татьяна Евгеньевна", "subject": "Русский язык и литература", "info": "Председатель ПЦК. Опытный преподаватель-филолог.", "photo": None},
    "zakirova": {"name": "Закирова Резеда Мадгатовна", "subject": "Инженерная графика", "info": "Заведующая дневным отделением, председатель ПЦК общепрофессиональных дисциплин.", "photo": None},
    "parfenov": {"name": "Парфенов Александр Вячеславович", "subject": "Основы алгоритмизации и программирования", "info": "Ведет разработку мобильных приложений. Преподаватель IT-дисциплин.", "photo": None},
    "safuilin": {"name": "Сафиулин Руслан Ринатович", "subject": "Компьютерные сети, поддержка ПО", "info": "Преподаватель специальных дисциплин в области IT.", "photo": None},
    "semin": {"name": "Семин Алексей Владимирович", "subject": "Детали машин", "info": "Председатель ПЦК по мехатронике. Преподаватель технических дисциплин.", "photo": None},
    "sinetova": {"name": "Синетова Рузиля Ганиевна", "subject": "Налоги, логистика, финансы", "info": "Кандидат экономических наук. Преподаватель экономических дисциплин.", "photo": None},
    "pulatova": {"name": "Пулатова Рушания Ренадовна", "subject": "Поварское дело", "info": "Председатель ПЦК по поварскому делу. Мастер производственного обучения.", "photo": None},
    "noskova": {"name": "Носкова Ирина Евгеньевна", "subject": "Логистика", "info": "Председатель ПЦК по логистике.", "photo": None},
    "musaeva": {"name": "Мусаева Залина Шамильевна", "subject": "Иностранный язык в профессиональной деятельности", "info": "Преподаватель английского языка в профессиональной сфере.", "photo": None},
    "khamidullina": {"name": "Хамидуллина С.В.", "subject": "Татарский язык в профессиональной деятельности", "info": "Преподаватель татарского языка.", "photo": None},
    "demidova": {"name": "Демидова В.М.", "subject": "Техническая механика", "info": "Преподаватель технической механики.", "photo": None},
    "zhuchkov": {"name": "Жучков С.П.", "subject": "Технологическое оборудование и оснастка", "info": "Преподаватель специальных технических дисциплин.", "photo": None},
    "nabiullin": {"name": "Набиуллин Фарит Вахитович", "subject": "МДК по ТО и ремонту автомобилей", "info": "Преподаватель automotive-дисциплин.", "photo": None},
    "nikiforov": {"name": "Никифоров Даниил Владимирович", "subject": "Электротехника и электроника", "info": "Преподаватель электротехнических дисциплин.", "photo": None},
    "alemasov": {"name": "Алемасов Евгений Павлович", "subject": "Программирование (дисциплины спеццикла)", "info": "Выпускник ЗМК. Победитель конкурса 'Лучший молодой преподаватель'.", "photo": None},
    "gorbunov": {"name": "Горбунов Д.В.", "subject": "Безопасность жизнедеятельности", "info": "Организатор ОБЖ. Преподаватель БЖД.", "photo": None},
    "malagin": {"name": "Малагин С.Ю.", "subject": "Физическая культура", "info": "Преподаватель физкультуры.", "photo": None},
    "trofimenko": {"name": "Трофименко А.С.", "subject": "Основы бережливого производства", "info": "Преподаватель дисциплин по бережливому производству.", "photo": None},
    "glazunova": {"name": "Глазунова Е.В.", "subject": "Основы финансовой грамотности", "info": "Преподаватель финансовой грамотности.", "photo": None},
    "khairullina": {"name": "Хайруллина Диляра Хамитовна", "subject": "История, Основы философии", "info": "Преподаватель гуманитарных дисциплин.", "photo": None},
    "moskalenko": {"name": "Москаленко Елена Викторовна", "subject": "Этика и психология профессиональной деятельности", "info": "Педагог-психолог. Ведет дисциплины по профессиональной этике.", "photo": None},
    "titova": {"name": "Титова Ирина Александровна", "subject": "Заместитель директора по учебной работе", "info": "Курирует учебный процесс.", "photo": None},
    "militsina": {"name": "Милицина Наталья Витальевна", "subject": "Заместитель директора по учебно-воспитательной работе", "info": "Курирует воспитательную работу.", "photo": None},
    "shtykov": {"name": "Штыков Александр Аркадьевич", "subject": "Заместитель директора по учебно-производственной работе", "info": "Курирует производственное обучение и практику.", "photo": None},
    "kalagin": {"name": "Калягин Игорь Игоревич", "subject": "Начальник отдела информационных технологий", "info": "Отвечает за IT-инфраструктуру колледжа.", "photo": None},
    "nurieva": {"name": "Нуриева Альбина Ильфатовна", "subject": "Советник директора по воспитанию", "info": "Организует воспитательную и внеурочную деятельность.", "photo": None},
    "shebanova": {"name": "Шебанова Яна Алексеевна", "subject": "Заместитель директора по научно-методической работе", "info": "Курирует методическую и научную работу.", "photo": None},
    "popov": {"name": "Попов Денис Александрович", "subject": "Заместитель директора по АХЧ", "info": "Отвечает за административно-хозяйственную часть.", "photo": None},
    "ilichev": {"name": "Ильичёв Владимир Александрович", "subject": "Зав. дневным отделением, руководитель Центра карьеры", "info": "Помогает студентам с трудоустройством и карьерой.", "photo": None}
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
    url = get_pdf_url(date)
    text = (
        f"📅 Расписание на {date.strftime('%d.%m.%Y')}:\n\n"
        f"🔗 [Открыть PDF]({url})\n\n"
        f"_Если ссылка не открывается — значит, на эту дату файла нет._"
    )
    query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=False)

# --- ЗАПУСК ---

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    print("Бот запущен.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
