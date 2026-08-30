async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    # ========== ГЛАВНЫЕ КНОПКИ ==========
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
    
    # ========== АДМИН-КНОПКИ ==========
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
            keyboard = []
            for q in questions[-10:]:
                status = "✅" if q["answered"] else "⏳"
                text += f"{status} #{q['id']} | {q['question'][:50]}...\n"
                text += f"   Пользователь: {q['username']}\n"
                text += f"   Дата: {q['timestamp']}\n\n"
                keyboard.append([InlineKeyboardButton(f"📩 Ответить на вопрос #{q['id']}", callback_data=f"answer_question_{q['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
            
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("answer_question_"):
        if user_id == ADMIN_ID:
            question_id = int(data.split("_")[2])
            context.user_data['answering_question'] = question_id
            await query.message.reply_text(
                f"✏️ Введите ответ для вопроса #{question_id}:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
            )
            context.user_data['state'] = 'waiting_answer'
    
    elif data == "admin_reports":
        if user_id == ADMIN_ID:
            reports = get_all_reports()
            if not reports:
                await query.message.reply_text("🔧 Сообщений о поломках пока нет.")
                return
            
            text = "🔧 *Сообщения о поломках:*\n\n"
            keyboard = []
            for r in reports[-10:]:
                text += f"📌 #{r['id']}\n"
                text += f"   👤 Пользователь: {r['username']}\n"
                text += f"   📝 Описание: {r['description'][:50]}...\n"
                text += f"   📅 Дата: {r['timestamp']}\n"
                if r.get('photo_file_id'):
                    text += f"   📸 Есть фото\n"
                text += "\n"
                keyboard.append([InlineKeyboardButton(f"📸 Просмотр поломки #{r['id']}", callback_data=f"view_report_{r['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
            
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("view_report_"):
        if user_id == ADMIN_ID:
            report_id = int(data.split("_")[2])
            reports = get_all_reports()
            report = None
            for r in reports:
                if r["id"] == report_id:
                    report = r
                    break
            
            if not report:
                await query.message.reply_text("❌ Поломка не найдена.")
                return
            
            text = f"📌 *Поломка #{report['id']}*\n\n"
            text += f"👤 Пользователь: {report['username']}\n"
            text += f"📝 Описание: {report['description']}\n"
            text += f"📅 Дата: {report['timestamp']}\n"
            text += f"📊 Статус: {report['status']}\n"
            
            # Отправляем описание
            await query.message.reply_text(text, parse_mode="Markdown")
            
            # Отправляем фото, если есть
            if report.get('photo_file_id'):
                try:
                    await query.message.reply_photo(
                        photo=report['photo_file_id'],
                        caption=f"📸 Фото к поломке #{report['id']}"
                    )
                except Exception as e:
                    await query.message.reply_text(f"❌ Не удалось загрузить фото: {e}")
            
            # Кнопки для ответа
            keyboard = [
                [InlineKeyboardButton(f"✏️ Ответить пользователю", callback_data=f"answer_report_{report_id}")],
                [InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_reports")],
            ]
            await query.message.reply_text(
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif data.startswith("answer_report_"):
        if user_id == ADMIN_ID:
            report_id = int(data.split("_")[2])
            context.user_data['answering_report'] = report_id
            await query.message.reply_text(
                f"✏️ Введите ответ для пользователя по поломке #{report_id}:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
            )
            context.user_data['state'] = 'waiting_answer_report'
    
    elif data == "admin_stats":
        if user_id == ADMIN_ID:
            total_q, answered_q, total_r = get_stats()
            text = f"📊 *Статистика:*\n\n"
            text += f"📋 Всего вопросов: {total_q}\n"
            text += f"✅ Отвечено: {answered_q}\n"
            text += f"⏳ Ожидают ответа: {total_q - answered_q}\n\n"
            text += f"🔧 Сообщений о поломках: {total_r}"
            
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]))
     
