import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
import requests

# Замените на ваш ключ Proxy API
PROXY_API_KEY = "sk-0lvLXdi3zZ9sN8SMuzdZsuqXNuYeCL0L"

# Базовый URL API Proxy API
BASE_URL = "https://api.proxyapi.ru/openai"

# Системная инструкция
SYSTEM_INSTRUCTION = """
Ты - умный помощник, способный генерировать код на разных языках, отвечать на вопросы и выполнять различные задачи. 
Старайся быть максимально информативным и полезным в своих ответах. 
"""

# Юзернейм канала, на который требуется подписаться
REQUIRED_CHANNEL_USERNAME = "@gptdale"  # Замените на юзернейм вашего канала

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Хранилище истории диалога
dialog_history = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Проверяем подписку на канал
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_USERNAME, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{REQUIRED_CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton("Проверить подписку", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Для доступа к боту, пожалуйста, подпишитесь на канал: {REQUIRED_CHANNEL_USERNAME}",
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            return
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        await update.message.reply_text("Произошла ошибка при проверке подписки.")

    await update.message.reply_text(
        "Привет! Этот бот открывает вам доступ к лучшим нейросетям для создания текста, изображений."
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет подписку пользователя на канал."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await update.callback_query.answer("Вы успешно подписаны на канал✅! Теперь вы можете использовать бота.")
            await update.callback_query.message.delete()  # Удаляем сообщение с кнопками
            await start(update, context)  # Запускаем стартовую функцию для нормальной работы бота
        else:
            await update.callback_query.answer("Вы не подписаны на канал❌.")
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        await update.callback_query.answer("Произошла ошибка при проверке подписки.")


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает историю диалога."""
    global dialog_history
    dialog_history.clear()
    await update.message.reply_text("🧹 Очищена история диалога!nnЧтобы перезапустить робота, напиши /start.")

async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщение пользователя и генерирует код или ответ."""
    user_input = update.message.text
    dialog_history.append({"role": "user", "content": user_input})
    # Отправляем сообщение "ИДЕТ ОБРАБОТКА ЗАПРОСА..."
    message = await update.message.reply_text("⏳ обрабатывает ваш запрос. Пожалуйста, подождите немного . . .")

    # Формируем запрос к Proxy API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_API_KEY}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}] + dialog_history  # Добавляем историю диалога
    }

    # Отправляем запрос и получаем ответ от Proxy API
    response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=data)

    # Проверяем успешный ответ
    if response.status_code == 200:
        generated_text = response.json()["choices"][0]["message"]["content"]
        dialog_history.append({"role": "assistant", "content": generated_text})

        # Отправляем ответ пользователю
        await message.edit_text(generated_text)
    else:
        await message.edit_text(f"Ошибка при обработке запроса: {response.text}")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Генерирует изображение по запросу пользователя."""
    user_input = ' '.join(context.args)

    if not user_input:
        await update.message.reply_text("Пожалуйста, укажите описание изображения.")
        return

    message = await update.message.reply_text("⏳ обрабатывает ваш запрос. Пожалуйста, подождите немного . . .")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_API_KEY}"
    }
    data = {
        "prompt": user_input,
        "n": 1,
        "size": "512x512"
    }

# Добавьте обработчики команд и запускайте приложение
application = ApplicationBuilder().token("7947990069:AAHnFmjsYaDtCiRqIJzCxpIgCqFdHYptIpU").build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("restart", restart))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_code))
application.add_handler(CommandHandler("generate_image", generate_image))

# Обработчик для кнопки проверки подписки
application.add_handler(CallbackQueryHandler(check_subscription))

# Запускаем бота
if __name__ == "__main__":
    application.run_polling()
