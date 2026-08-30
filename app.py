import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= НАСТРОЙКИ =================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ Токен не найден!")
    exit(1)

ADMIN_ID = 1240591787

logging.basicConfig(level=logging.INFO)

# ================= БАЗА ДАННЫХ (JSON) =================
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"questions": [], "reports": [], "counter": 0}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_question(user_id, username, question):
    data = load_data()
    data["counter"] += 1
    data["questions"].append({
        "id": data["counter"],
        "user_id": user_id,
        "username": username or "Аноним",
        "question": question,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answered": False
    })
    save_data(data)
    return data["counter"]

def get_all_questions():
    data = load_data()
    return data["questions"]

# ================= КЛАВИАТУРЫ =================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("❓ Задать вопрос", callback_data="ask")],
        [InlineKeyboardButton("🔧 Сообщить о поломке", callback_data="report")],
        [InlineKeyboardButton("📚 FAQ", callback_data="faq")],
        [InlineKeyboardButton("📖 Учебный процесс", callback_data="study")],
        [InlineKeyboardButton("🗺️ Карта корпуса", callback_data="map")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Все вопросы", callback_data="admin_q")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= ОБРАБОТЧИКИ =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome = """Привет, студент! 👋

Этот бот создан Студенческим советом ВШУ.

Здесь ты можешь:
- задать вопрос по учёбе
- сообщить о поломке в корпусе
- узнать полезную информацию

Выберите действие:"""
    
    await update.message.reply_text(welcome, reply_markup=get_main_keyboard())
    if user_id == ADMIN_ID:
        await update.message.reply_text("👋 Админ-панель:", reply_markup=get_admin_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    if data == "ask":
        await query.message.reply_text("✏️ Напишите ваш вопрос:")
        context.user_data['state'] = 'question'
    
    elif data == "report":
        await query.message.reply_text("📸 Пришлите фото и описание поломки:")
        context.user_data['state'] = 'report'
        context.user_data['report_photos'] = []
    
    elif data == "faq":
        faq_text = """*Часто задаваемые вопросы*

*1. Получение скидки:*  
Скидка предоставляется на семестр для студентов очной формы обучения. Размер - от 10% до 100%.

*2. Что делать, если заболел во время сессии?*  
Необходимо предоставить справку в кабинет 321.

*3. Где смотреть расписание занятий?*  
На сайте ruz.fa.ru или в приложении «Кампус».

*4. Оплата материнским капиталом:*  
Обратиться в кабинет 321 к Л. И. Карзаловой.

*5. Куда обратиться за справками?*  
В студенческий офис (Ленинградский проспект, 53)."""
        await query.message.reply_text(faq_text, parse_mode="Markdown")
    
    elif data == "study":
        study_text = """*Учебный процесс*

*Экзамены*  
Формат: письменный, устный или электронный.  
Продолжительность: 1,5 часа (письменный) или 10-12 минут (устный).

*Правила*  
Запрещены шпаргалки и телефоны. При себе иметь паспорт.

*Баллы*  
Максимум - 100 баллов:  
- 40 баллов - работа в семестре  
- 60 баллов - экзамен

*Пересдача*  
Зимой (конец января) и летом (конец августа).

*Контакты*  
Деканат: Верхняя Масловка, 15  
8 (495) 249-53-00  
hsm@fa.ru"""
        await query.message.reply_text(study_text, parse_mode="Markdown")
    
    elif data == "map":
        map_paths = ["maps/1_etazh.jpg", "maps/2_etazh.jpg", "maps/3_etazh.jpg", 
                     "maps/4_etazh.jpg", "maps/5_etazh.jpg", "maps/komputer_korpus.jpg"]
        
        sent_first = False
        for path in map_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    if not sent_first:
                        await query.message.reply_photo(photo=f, caption="🗺️ Схемы корпусов:")
                        sent_first = True
                    else:
                        await query.message.reply_photo(photo=f)
        if not sent_first:
            await query.message.reply_text("❌ Карты временно недоступны.")
    
    elif data == "back":
        await query.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        if user_id == ADMIN_ID:
            await query.message.reply_text("Админ-панель:", reply_markup=get_admin_keyboard())
    
    elif data == "admin_q" and user_id == ADMIN_ID:
        questions = get_all_questions()
        if not questions:
            await query.message.reply_text("📋 Вопросов пока нет.")
            return
        text = "📋 *Все вопросы:*\n\n"
        for q in questions[-10:]:  # Последние 10
            status = "✅" if q["answered"] else "⏳"
            text += f"{status} #{q['id']} | {q['question'][:40]}...\n"
            text += f"   От: {q['username']} | {q['timestamp']}\n\n"
        await query.message.reply_text(text, parse_mode="Markdown")
    
    elif data == "admin_stats" and user_id == ADMIN_ID:
        questions = get_all_questions()
        total = len(questions)
        answered = sum(1 for q in questions if q["answered"])
        text = f"📊 *Статистика:*\n\n"
        text += f"📋 Всего вопросов: {total}\n"
        text += f"✅ Отвечено: {answered}\n"
        text += f"⏳ Ожидают: {total - answered}"
        await query.message.reply_text(text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    user_id = update.effective_user.id
    text = update.message.text
    username = update.effective_user.username or "Аноним"
    
    if state == 'question':
        q_id = save_question(user_id, username, text)
        await update.message.reply_text("✅ Спасибо за вопрос! Ответ придёт в течение 2-х дней.")
        context.user_data['state'] = None
        if user_id != ADMIN_ID:
            await update.message.bot.send_message(
                ADMIN_ID, 
                f"📩 *Новый вопрос #{q_id}*\n"
                f"От: @{username}\n"
                f"Текст: {text[:200]}"
            )
    
    elif state == 'report':
        await update.message.reply_text("✅ Спасибо! Мы разберемся с проблемой.")
        context.user_data['state'] = None
        if user_id != ADMIN_ID:
            await update.message.bot.send_message(
                ADMIN_ID,
                f"🔧 *Новая поломка*\n"
                f"От: @{username}\n"
                f"Описание: {text[:200]}"
            )
    
    else:
        await update.message.reply_text("Используйте кнопки меню.", reply_markup=get_main_keyboard())

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'report':
        photo = update.message.photo[-1]
        context.user_data.setdefault('report_photos', []).append(photo.file_id)
        await update.message.reply_text("📸 Фото получено! Теперь напишите описание поломки.")
    else:
        await update.message.reply_text("Используйте кнопку 'Сообщить о поломке'.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = None
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_keyboard())

# ================= ЗАПУСК =================
def main():
    print("🚀 БОТ ЗАПУЩЕН!")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("✅ БОТ ГОТОВ К РАБОТЕ!")
    app.run_polling()

if __name__ == "__main__":
    main()
