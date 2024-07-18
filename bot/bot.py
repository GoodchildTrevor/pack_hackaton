from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters)

from elasticsearch import Elasticsearch

from dotenv import load_dotenv
import os
import joblib

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

vectorizer = joblib.load('../database/tfidf_vectorizer.joblib')
svd = joblib.load('../database/svd_model.joblib')

def query_to_elastic (text):

    vector = vectorizer.transform([text])
    query_vector = svd.transform(vector)

    query_vector_list = query_vector[0].tolist()

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                "params": {"query_vector": query_vector_list}
            }
        }
    }

    response = es.search(
        index="documents",
        body={
            "size": 1,
            "query": script_query,
            "_source": ["filename", "paragraph", "department"]
        }
    )

    for hit in response['hits']['hits']:
        score = (hit['_score'] - 1)*100
        filename = hit['_source']['filename']

    return score, filename


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Попробовать", callback_data='start_interaction')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Тест')


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['ready_for_classification'] = True
    await query.edit_message_text(text="Начать")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and not update.message.text.startswith('/'):
        if context.user_data.get('ready_for_classification', False):
            score, filename = query_to_elastic(update.message.text)
            await update.message.reply_text(f'Самый подходящий файл: \n {filename} \n со сходством {score:.0f}%')
            # После отправки классификации устанавливаем флаг готовности к новой классификации
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
app.add_handler(CallbackQueryHandler(button))

# Обработчик для всех текстовых сообщений
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback=echo))

app.run_polling()