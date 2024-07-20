from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
import joblib

from seacrh_test import ElasticQuery

import warnings
warnings.filterwarnings("ignore")

load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")
password = os.getenv("ELASTIC_PASSWORD")

es = Elasticsearch(
    ["https://localhost:9200"],
    http_auth=('elastic', password),
    verify_certs=False
)

vectorizer_drk = joblib.load('../database/tfidf_vectorizer.joblib')
svd = joblib.load('../database/svd_model.joblib')

DEPARTMENTS = ["DRK", "CMK", "OTR", "FT", "FTL"]

DEPARTMETS_DICT = {
    "DRK": vectorizer_drk,
    "CMK": vectorizer_drk,
    "OTR": vectorizer_drk,
    "FT": vectorizer_drk,
    "FTL": vectorizer_drk
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data='start_interaction')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Добро пожаловать! Нажмите кнопку "Начать", чтобы продолжить.', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Спрашиваем пользователя из какого он отдела
    keyboard = [[InlineKeyboardButton(department, callback_data=department)] for department in DEPARTMENTS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Из какого вы отдела?", reply_markup=reply_markup)


async def handle_department_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['department'] = query.data
    context.user_data['ready_for_classification'] = True
    await query.edit_message_text(text=f"Вы выбрали отдел: {query.data}. Теперь введите текст для классификации.")


async def input_output(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and not update.message.text.startswith('/'):
        if context.user_data.get('ready_for_classification', False):
            query = update.message.text
            department = context.user_data.get('department', 'Unknown')
            vectorizer = DEPARTMETS_DICT[department]
            query_to_elastic = ElasticQuery(query=query, size=1, svd=svd, vectorizer=vectorizer)
            score, filename = query_to_elastic.get_results()
            await update.message.reply_text(f'Самый подходящий файл: \n {filename} \n со сходством {score:.0f}%')

            # Устанавливаем флаг готовности к новой классификации
            context.user_data['ready_for_classification'] = False

            # Отправляем кнопку для нового запроса
            keyboard = [
                [InlineKeyboardButton("Классифицировать другой текст", callback_data='start_interaction')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Нажмите кнопку ниже, чтобы начать новую классификацию.", reply_markup=reply_markup)
        else:
            # Если флаг не установлен, предлагаем пользователю начать классификацию
            keyboard = [
                [InlineKeyboardButton("Попробовать", callback_data='start_interaction')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Нажмите кнопку ниже, чтобы начать классификацию текста.", reply_markup=reply_markup)

app = ApplicationBuilder().token(f"{telegram_token}").build()

app.add_handler(CommandHandler('start', start))

# Обработчик для кнопок
app.add_handler(CallbackQueryHandler(button, pattern='start_interaction'))
app.add_handler(CallbackQueryHandler(handle_department_selection, pattern='^(DRK|CMK|OTR|FT|FTL)$'))

# Обработчик для всех текстовых сообщений
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback=input_output))

app.run_polling()
