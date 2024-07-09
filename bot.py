from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters)

from dotenv import load_dotenv
import os

load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")


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
            sequence_to_classify = update.message.text
            await update.message.reply_text(sequence_to_classify)
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