import os
import json
import logging
import threading
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ================= НАСТРОЙКИ =================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ Токен не найден! Добавьте TELEGRAM_BOT_TOKEN в переменные окружения Render.")
    exit(1)

ADMIN_ID = 1240591787

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= FLASK =================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 Бот работает!", 200

@flask_app.route('/health')
def health():
    return "OK", 200

# ================= БАЗА ДАННЫХ =================
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
    return data["questions"]

def get_all_reports():
    data = load_data()
    return data["reports"]

def get_unanswered_questions():
    data = load_data()
    return [q for q in data["questions"] if not q["answered"]]

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
            return q
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
    
    welcome_text = """Привет, студент! 👋

Этот бот был создан Студенческим советом ВШУ, чтобы сделать твоё обучение комфортнее. Здесь ты можешь:

- задать вопрос по учёбе;
- сообщить о поломке в корпусе (сломанная мебель, неработающий свет и др.).

Просто выбери нужную опцию в меню и напиши свой вопрос, а мы постараемся помочь. Ответ придёт в течение 2-х дней.

В случае использования нецензурной лексики, оскорблений, некорректных формулировок или предоставления ложной информации, сообщение будет заблокировано, и ответа не последует.
Бот гарантирует полную конфиденциальность и анонимность при выборе этой опции.

Твой вклад важен - вместе мы сделаем учёбу комфортнее!"""

    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👋 Привет, Админ! Панель управления:",
            reply_markup=get_admin_keyboard()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    if data == "ask_question":
        await query.message.reply_text(
            "✏️ Задайте любой вопрос. Мы постараемся ответить в течение 2-х дней.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )
        context.user_data['state'] = 'waiting_question'
    
    elif data == "report_issue":
        await query.message.reply_text(
            "📸 Пришлите фотографию и описание поломки (например: стул, 440 кабинет)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )
        context.user_data['state'] = 'waiting_report'
        context.user_data['report_photos'] = []
    
    elif data == "faq":
        faq_text = """*Часто задаваемые вопросы*

*1. Получение скидки:*  
Скидка предоставляется на семестр для студентов очной формы обучения бакалавриата и магистратуры. Её размер - от 10% до 100% от стоимости обучения - зависит от места студента в рейтинге по итогам сессии.

*2. Что делать, если заболел во время сессии?*  
Если вы пропустили зачёт или экзамен по болезни, для того чтобы неявка была признана уважительной, необходимо сразу после выздоровления предоставить справку Л. И. Карзаловой в кабинет 321.

*3. Где смотреть расписание занятий?*  
Расписание занятий в первую очередь публикуется на сайте ruz.fa.ru. Для удобства его также можно смотреть в приложениях «Кампус».

*4. Оплата материнским капиталом или образовательным кредитом:*  
Для оплаты обучения с помощью материнского капитала или образовательного кредита необходимо сначала обратиться в кабинет 321 к Л. И. Карзаловой: для оформления кредита - за счётом, для использования маткапитала - за отсрочкой. После этого со счётом необходимо обратиться в московское отделение Сбербанка.

*5. Куда обратиться за получением справок?*  
За справками нужно обращаться в студенческий офис (г. Москва, Ленинградский проспект, д. 53) или заказать их на сайте Финансового университета.

*6. Что такое Студенческий совет?*  
Студенческий совет Финансового университета представляет интересы учащихся, способствует развитию их навыков, организует мероприятия и информирует студентов через медиаканалы.

*7. Что даёт участие в Студсовете?*  
Участие в студенческом совете развивает профессиональные навыки и личные качества, которые ценятся работодателями, а также даёт возможность стать частью дружного коллектива."""
        
        await query.message.reply_text(faq_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))
    
    elif data == "study_process":
        study_text = """*Учебный процесс*

*Экзамены*  
Формат: письменный, устный или электронный (на компьютере в университете).  
Продолжительность:  
- письменный/электронный - 1,5 часа;  
- устный - 25 минут на подготовку и 10-12 минут на ответ.  
Дату экзамена назначает Студенческий офис (учебная часть).

*Правила*  
- На экзамене запрещены шпаргалки, неразрешённые материалы, телефоны, смарт-часы и другие средства связи.  
- За использование запрещённых материалов студент может быть удалён с экзамена и получить «неудовлетворительно» без пересдачи в основной период.  
- За нарушение порядка преподаватель может удалить студента с экзамена.  
- При себе необходимо иметь паспорт или другой документ, удостоверяющий личность.  
- При опоздании время экзамена не продлевается.  
- Если студент проспал или опоздал по неуважительной причине, возможность сдачи с другой группой решается индивидуально.

*Баллы*  
Максимум за дисциплину - 100 баллов:  
- 40 баллов - работа в семестре (2 ТКУ по 20 баллов);  
- 60 баллов - экзамен или зачёт.  
По дисциплине с экзаменом итоговые баллы переводятся в 5-балльную оценку. По зачёту выставляется «зачтено» или «не зачтено».

*Апелляция*  
Апелляция подаётся при:  
- технической ошибке в подсчёте баллов;  
- ошибке или неоднозначности в задании;  
- нарушении установленной процедуры экзамена.  
Несогласие с полученной оценкой само по себе основанием для апелляции не является.  
Апелляция подаётся в установленные сроки, обычно в течение 1-2 рабочих дней после объявления результатов.

*Пересдача*  
При оценке «неудовлетворительно» студент направляется на пересдачу.  
Периоды пересдач:  
- зимний - конец января;  
- летний - конец августа.  
Если экзамен не сдан после пересдачи, студент направляется на комиссию. При повторном неудовлетворительном результате возможно отчисление за академическую неуспеваемость.

*Контакты*  
Деканат  
Верхняя Масловка, 15  
8 (495) 249-53-00  
hsm@fa.ru  
Пн-пт: 09:00-18:00, сб: 09:00-13:30

Учебный отдел: 6648, 5323, 5372  
Партнёры: 5266, 1941  
Научная работа: 6644  
Воспитательная работа: 5343, 5344

Студенческий офис  
Ленинградский проспект, 53  
Помощь со справками, документами, переводами, расписанием, академическим отпуском, пересдачами и учебными вопросами.

Охрана / пропуск  
+7 (499) 553-13-82  
Утеря, кража или поломка электронной карты.

Международный отдел  
inter@fa.ru"""
        
        await query.message.reply_text(study_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))
    
    elif data == "map":
        map_paths = [
            "maps/1_etazh.jpg",
            "maps/2_etazh.jpg",
            "maps/3_etazh.jpg",
            "maps/4_etazh.jpg",
            "maps/5_etazh.jpg",
            "maps/komputer_korpus.jpg"
        ]
        
        valid_paths = []
        for path in map_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                logger.warning(f"Файл карты не найден: {path}")
        
        if not valid_paths:
            await query.message.reply_text("❌ Карты временно недоступны. Попробуйте позже.")
            return
        
        for i, path in enumerate(valid_paths):
            try:
                with open(path, 'rb') as f:
                    if i == 0:
                        await query.message.reply_photo(photo=f, caption="🗺️ Схемы корпусов:")
                    else:
                        await query.message.reply_photo(photo=f)
            except Exception as e:
                logger.error(f"Ошибка при отправке карты {path}: {e}")
        
        await query.message.reply_text("Все карты отправлены!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))
    
    elif data == "back_to_main":
        await query.message.reply_text("Главное меню:", reply_markup=get_main_keyboard())
        if user_id == ADMIN_ID:
            await query.message.reply_text("Админ-панель:", reply_markup=get_admin_keyboard())
    
    elif data == "admin_panel":
        if user_id == ADMIN_ID:
            await query.message.reply_text("Панель администратора:", reply_markup=get_admin_keyboard())
    
    elif data == "admin_questions":
        if user_id == ADMIN_ID:
            questions = get_all_questions()
            if not questions:
                await query.message.reply_text("📋 Вопросов пока нет.")
                return
            
            text = "📋 *Все вопросы:*\n\n"
            for q in questions[-10:]:
                status = "✅" if q["answered"] else "⏳"
                text += f"{status} #{q['id']} | {q['question'][:50]}...\n"
                text += f"   Пользователь: {q['username']}\n"
                text += f"   Дата: {q['timestamp']}\n\n"
            
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
    
    elif data == "admin_reports":
        if user_id == ADMIN_ID:
            reports = get_all_reports()
            if not reports:
                await query.message.reply_text("🔧 Сообщений о поломках пока нет.")
                return
            
            text = "🔧 *Сообщения о поломках:*\n\n"
            for r in reports[-10:]:
                text += f"#{r['id']} | {r['description'][:50]}...\n"
                text += f"   Пользователь: {r['username']}\n"
                text += f"   Дата: {r['timestamp']}\n"
                text += f"   Статус: {r['status']}\n"
                if r.get('photo_file_id'):
                    text += f"   📸 Есть фото\n"
                text += "\n"
            
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
    
    elif data == "admin_stats":
        if user_id == ADMIN_ID:
            total_q, answered_q, total_r = get_stats()
            text = f"📊 *Статистика:*\n\n"
            text += f"📋 Всего вопросов: {total_q}\n"
            text += f"✅ Отвечено: {answered_q}\n"
            text += f"⏳ Ожидают ответа: {total_q - answered_q}\n\n"
            text += f"🔧 Сообщений о поломках: {total_r}"
            
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
    
    elif data == "admin_answer":
        if user_id == ADMIN_ID:
            unanswered = get_unanswered_questions()
            if not unanswered:
                await query.message.reply_text("✅ Нет неотвеченных вопросов.")
                return
            
            text = "✏️ *Выберите вопрос для ответа:*\n\n"
            keyboard = []
            for q in unanswered[:10]:
                text += f"#{q['id']} | {q['question'][:50]}...\n"
                text += f"   Пользователь: {q['username']}\n"
                text += f"   Дата: {q['timestamp']}\n\n"
                keyboard.append([InlineKeyboardButton(f"#{q['id']} - {q['question'][:30]}...", callback_data=f"answer_{q['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
            
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("answer_"):
        if user_id == ADMIN_ID:
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
    username = update.effective_user.username or "Аноним"
    
    bad_words = ['мат', 'хуй', 'пизда', 'бля', 'сука', 'залупа', 'мудак', 'редиска', 'нах', 'еба']
    has_bad_words = any(word in text.lower() for word in bad_words)
    
    if has_bad_words:
        await update.message.reply_text(
            "⚠️ Ваше сообщение содержит недопустимые выражения и было заблокировано.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
        )
        context.user_data['state'] = None
        return
    
    if state == 'waiting_question':
        question_id = save_question(user_id, username, text)
        await update.message.reply_text(
            "✅ Спасибо за вопрос. Ответ придёт в течение 2-х дней.",
            reply_markup=get_main_keyboard()
        )
        context.user_data['state'] = None
        
        if user_id != ADMIN_ID:
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"📩 *Новый вопрос #{question_id}*\n\n"
                    f"От: @{username}\n"
                    f"Вопрос: {text[:200]}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить админа: {e}")
    
    elif state == 'waiting_report':
        photos = context.user_data.get('report_photos', [])
        photo_id = photos[0] if photos else None
        report_id = save_report(user_id, username, text, photo_id)
        
        await update.message.reply_text(
            "✅ Спасибо за инициативу! Мы разберемся с проблемой.",
            reply_markup=get_main_keyboard()
        )
        context.user_data['state'] = None
        context.user_data['report_photos'] = []
        
        if user_id != ADMIN_ID:
            try:
                admin_text = f"🔧 *Новая поломка #{report_id}*\n\n"
                admin_text += f"От: @{username}\n"
                admin_text += f"Описание: {text[:200]}"
                if photo_id:
                    admin_text += f"\n📸 Есть фото"
                
                await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
                
                if photo_id:
                    await context.bot.send_photo(ADMIN_ID, photo_id, caption=f"Фото к поломке #{report_id}")
            except Exception as e:
                logger.error(f"Не удалось уведомить админа: {e}")
    
    elif state == 'waiting_answer':
        if user_id == ADMIN_ID:
            question_id = context.user_data.get('answering_question')
            if question_id:
                answer_question(question_id, text)
                q_data = get_question_by_id(question_id)
                if q_data:
                    user_to_answer = q_data['user_id']
                    try:
                        await context.bot.send_message(
                            user_to_answer,
                            f"📩 *Ответ на ваш вопрос #{question_id}:*\n\n{text}",
                            parse_mode="Markdown"
                        )
                        await update.message.reply_text(
                            f"✅ Ответ на вопрос #{question_id} отправлен пользователю.",
                            reply_markup=get_admin_keyboard()
                        )
                    except Exception as e:
                        await update.message.reply_text(
                            f"⚠️ Не удалось отправить ответ пользователю. Ответ сохранён.",
                            reply_markup=get_admin_keyboard()
                        )
                else:
                    await update.message.reply_text(f"⚠️ Вопрос #{question_id} не найден.", reply_markup=get_admin_keyboard())
                
                context.user_data['state'] = None
                context.user_data['answering_question'] = None
            else:
                await update.message.reply_text("⚠️ Не выбран вопрос для ответа.", reply_markup=get_admin_keyboard())
    
    else:
        await update.message.reply_text(
            "Используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'waiting_report':
        photo = update.message.photo[-1]
        file_id = photo.file_id
        context.user_data.setdefault('report_photos', []).append(file_id)
        await update.message.reply_text("📸 Фото получено. Теперь напишите описание поломки.")
    else:
        await update.message.reply_text(
            "Сейчас бот не ожидает фото. Используйте кнопку 'Сообщить о поломке'.",
            reply_markup=get_main_keyboard()
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = None
    context.user_data['answering_question'] = None
    context.user_data['report_photos'] = []
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_keyboard())

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    except:
        pass

# ================= ЗАПУСК БОТА В ПОТОКЕ =================
def run_bot():
    # СОЗДАЁМ НОВЫЙ EVENT LOOP (ЭТО ИСПРАВЛЯЕТ ОШИБКУ!)
    asyncio.set_event_loop(asyncio.new_event_loop())
    
    print("🚀 БОТ ЗАПУЩЕН!")
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    
    print("✅ БОТ ГОТОВ К РАБОТЕ!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ================= ОСНОВНОЙ ЗАПУСК =================
if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("🐍 Бот запущен в фоновом потоке")
    
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Запуск веб-сервера на порту {port}")
    flask_app.run(host="0.0.0.0", port=port)
