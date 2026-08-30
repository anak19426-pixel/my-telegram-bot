import os
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= НАСТРОЙКИ =================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: Переменная окружения TELEGRAM_BOT_TOKEN не установлена!", file=sys.stderr)
    sys.exit(1)

ADMIN_ID = 1240591787

# ================= ЛОГИРОВАНИЕ =================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= РАБОТА С ДАННЫМИ (JSON) =================
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"questions": [], "reports": [], "question_counter": 0, "report_counter": 0}
    return {"questions": [], "reports": [], "question_counter": 0, "report_counter": 0}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_question(user_id, username, question):
    data = load_data()
    data["question_counter"] += 1
    question_data = {
        "id": data["question_counter"],
        "user_id": user_id,
        "username": username or "Аноним",
        "question": question,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answered": False,
        "answer": ""
    }
    data["questions"].append(question_data)
    save_data(data)
    return data["question_counter"]

def save_report(user_id, username, description, photo_file_id=None):
    data = load_data()
    data["report_counter"] += 1
    report_data = {
        "id": data["report_counter"],
        "user_id": user_id,
        "username": username or "Аноним",
        "description": description,
        "photo_file_id": photo_file_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "new"
    }
    data["reports"].append(report_data)
    save_data(data)
    return data["report_counter"]

def get_all_questions():
    data = load_data()
    return [(q["id"], q["user_id"], q["username"], q["question"], q["timestamp"], q["answered"]) for q in data["questions"]]

def get_all_reports():
    data = load_data()
    return [(r["id"], r["user_id"], r["username"], r["description"], r["photo_file_id"], r["timestamp"], r["status"]) for r in data["reports"]]

def get_unanswered_questions():
    data = load_data()
    return [(q["id"], q["user_id"], q["username"], q["question"], q["timestamp"]) for q in data["questions"] if not q["answered"]]

def answer_question(question_id, answer_text):
    data = load_data()
    for q in data["questions"]:
        if q["id"] == question_id:
            q["answered"] = True
            q["answer"] = answer_text
            break
    save_data(data)

def get_question_by_id(question_id):
    data = load_data()
    for q in data["questions"]:
        if q["id"] == question_id:
            return (q["user_id"], q["question"])
    return None

def get_stats():
    data = load_data()
    total_questions = len(data["questions"])
    answered_questions = sum(1 for q in data["questions"] if q["answered"])
    total_reports = len(data["reports"])
    return total_questions, answered_questions, total_reports

# ================= КЛАВИАТУРЫ =================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question")],
        [InlineKeyboardButton("🔧 Сообщить о поломке", callback_data="report_issue")],
        [InlineKeyboardButton("📚 FAQ", callback_data="faq")],
        [InlineKeyboardButton("📖 Учебный процесс", callback_data="study_process")],
        [InlineKeyboardButton("🗺️ Карта корпуса", callback_data="map")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Все вопросы", callback_data="admin_questions")],
        [InlineKeyboardButton("🔧 Все поломки", callback_data="admin_reports")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("✏️ Ответить на вопрос", callback_data="admin_answer")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= ОБРАБОТЧИКИ =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = """Привет, студент!

Этот бот был создан Студенческим советом ВШУ, чтобы сделать твоё обучение комфортнее. Здесь ты можешь:

- задать вопрос по учёбе;
- сообщить о поломке в корпусе (сломанная мебель, неработающий свет и др.).

Просто выбери нужную опцию в меню и напиши свой вопрос, а мы постараемся помочь. Ответ придёт в течение 2-х дней.

В случае использования нецензурной лексики, оскорблений, некорректных формулировок или предоставления ложной информации, сообщение будет заблокировано, и ответа не последует.

Твой вклад важен - вместе мы сделаем учёбу комфортнее!"""
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())
    if user_id == ADMIN_ID:
        await update.message.reply_text("👋 Привет, Админ! Панель управления:", reply_markup=get_admin_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    if data == "ask_question":
        await query.message.reply_text(
            "✏️ Задайте любой вопрос. Ответ придёт в течение 2-х дней.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )
        context.user_data['state'] = 'waiting_question'
    
    elif data == "report_issue":
        await query.message.reply_text(
            "📸 Пришлите фотографию и описание поломки",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )
        context.user_data['state'] = 'waiting_report'
        context.user_data['report_photos'] = []
    
    elif data == "faq":
        faq_text = """*Часто задаваемые вопросы*

*1. Получение скидки:*  
Скидка предоставляется на семестр для студентов очной формы обучения.

*2. Что делать, если заболел во время сессии?*  
Необходимо предоставить справку в кабинет 321.

*3. Где смотреть расписание занятий?*  
На сайте ruz.fa.ru или в приложении «Кампус»."""
        await query.message.reply_text(faq_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))
    
    elif data == "study_process":
        study_text = """*Учебный процесс*

*Экзамены*  
Формат: письменный, устный или электронный.  
Продолжительность: 1,5 часа (письменный) или 10-12 минут (устный).

*Правила*  
Запрещены шпаргалки и телефоны.

*Баллы*  
Максимум - 100 баллов."""
        await query.message.reply_text(study_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))
    
    elif data == "map":
        map_paths = ["maps/1_etazh.jpg", "maps/2_etazh.jpg", "maps/3_etazh.jpg"]
        for path in map_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    await query.message.reply_photo(photo=f)
        await query.message.reply_text("🗺️ Карты корпусов", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))
    
    elif data == "back_to_main":
        await query.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        if user_id == ADMIN_ID:
            await query.message.reply_text("Админ-панель:", reply_markup=get_admin_keyboard())
    
    elif data == "admin_panel" and user_id == ADMIN_ID:
        await query.message.reply_text("Панель администратора:", reply_markup=get_admin_keyboard())
    
    elif data == "admin_questions" and user_id == ADMIN_ID:
        questions = get_all_questions()
        if not questions:
            await query.message.reply_text("📋 Вопросов пока нет.")
            return
        text = "📋 *Все вопросы:*\n\n"
        for q in questions:
            status = "✅" if q[5] else "⏳"
            text += f"{status} #{q[0]} | {q[3][:50]}...\n"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
    
    elif data == "admin_reports" and user_id == ADMIN_ID:
        reports = get_all_reports()
        if not reports:
            await query.message.reply_text("🔧 Сообщений о поломках пока нет.")
            return
        text = "🔧 *Сообщения о поломках:*\n\n"
        for r in reports:
            text += f"#{r[0]} | {r[3][:50]}...\n"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
    
    elif data == "admin_stats" and user_id == ADMIN_ID:
        total_q, answered_q, total_r = get_stats()
        text = f"📊 *Статистика:*\n\n📋 Всего вопросов: {total_q}\n✅ Отвечено: {answered_q}\n⏳ Ожидают ответа: {total_q - answered_q}\n\n🔧 Сообщений о поломках: {total_r}"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
    
    elif data == "admin_answer" and user_id == ADMIN_ID:
        unanswered = get_unanswered_questions()
        if not unanswered:
            await query.message.reply_text("✅ Нет неотвеченных вопросов.")
            return
        keyboard = []
        for q in unanswered:
            keyboard.append([InlineKeyboardButton(f"#{q[0]} - {q[3][:30]}...", callback_data=f"answer_{q[0]}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
        await query.message.reply_text("✏️ Выберите вопрос:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("answer_") and user_id == ADMIN_ID:
        question_id = int(data.split("_")[1])
        context.user_data['answering_question'] = question_id
        await query.message.reply_text(
            f"✏️ Введите ответ для вопроса #{question_id}:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
        )
        context.user_data['state'] = 'waiting_answer'

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')
    
    if state == 'waiting_question':
        username = update.effective_user.username or "Аноним"
        save_question(user_id, username, text)
        await update.message.reply_text("✅ Спасибо за вопрос. Ответ придёт в течение 2-х дней.", reply_markup=get_main_keyboard())
        context.user_data['state'] = None
        if user_id != ADMIN_ID:
            try:
                await context.bot.send_message(ADMIN_ID, f"📩 Новый вопрос от @{username}:\n{text[:100]}...")
            except:
                pass
    
    elif state == 'waiting_report':
        username = update.effective_user.username or "Аноним"
        photos = context.user_data.get('report_photos', [])
        photo_id = photos[0] if photos else None
        save_report(user_id, username, text, photo_id)
        await update.message.reply_text("✅ Спасибо за инициативу!", reply_markup=get_main_keyboard())
        context.user_data['state'] = None
        context.user_data['report_photos'] = []
        if user_id != ADMIN_ID:
            try:
                await context.bot.send_message(ADMIN_ID, f"🔧 Новая поломка от @{username}:\n{text}")
            except:
                pass
    
    elif state == 'waiting_answer' and user_id == ADMIN_ID:
        question_id = context.user_data.get('answering_question')
        if question_id:
            answer_question(question_id, text)
            q_data = get_question_by_id(question_id)
            if q_data:
                try:
                    await context.bot.send_message(q_data[0], f"📩 Ответ на ваш вопрос:\n\n{text}")
                    await update.message.reply_text(f"✅ Ответ на вопрос #{question_id} отправлен.", reply_markup=get_admin_keyboard())
                except:
                    await update.message.reply_text(f"⚠️ Не удалось отправить ответ.", reply_markup=get_admin_keyboard())
            context.user_data['state'] = None
            context.user_data['answering_question'] = None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'waiting_report':
        photo = update.message.photo[-1]
        context.user_data.setdefault('report_photos', []).append(photo.file_id)
        await update.message.reply_text("📸 Фото получено. Напишите описание поломки.")
    else:
        await update.message.reply_text("Используйте кнопку 'Сообщить о поломке'.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = None
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_keyboard())

# ================= СОЗДАНИЕ ВЕБ-СЕРВЕРА =================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

# ================= ЗАПУСК БОТА =================
def main():
    """Запуск бота"""
    Path("maps").mkdir(exist_ok=True)
    print("🚀 БОТ ЗАПУЩЕН!")
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("✅ БОТ ГОТОВ К РАБОТЕ!")
    application.run_polling()

if __name__ == "__main__":
    # Запускаем бот в отдельном потоке
    import threading
    bot_thread = threading.Thread(target=main, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Запуск веб-сервера на порту {port}")
    app.run(host="0.0.0.0", port=port)
