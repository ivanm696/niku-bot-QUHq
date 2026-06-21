import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from groq import Groq

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ПРАВИЛЬНЫЙ БЛОК ЗАГРУЗКИ ПЕРЕМЕННЫХ
try:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    if not BOT_TOKEN or not GROQ_API_KEY:
        raise ValueError("Критическая ошибка: Переменные BOT_TOKEN или GROQ_API_KEY не заданы на Render!")
except Exception as e:
    logging.error('Error loading environment variables: %s', e)
    raise

# Инициализация клиентов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

# Хранилище контекста (память до 20 сообщений)
user_context = {}

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_context[message.from_user.id] = []
    await message.answer(
        "🤖 **Привет! Я NicuAI** — твой ассистент на базе Llama-3.3-70b.\n"
        "Задай мне любой вопрос, и я отвечу!"
    )

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_context:
        user_context[user_id] = []
        
    user_context[user_id].append({"role": "user", "content": message.text})
    
    # Ограничиваем контекст до 20 сообщений
    if len(user_context[user_id]) > 20:
        user_context[user_id] = user_context[user_id][-20:]
        
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        system_prompt = {"role": "system", "content": "You are NicuAI, a helpful AI assistant. Answer in the language the user uses."}
        messages_to_send = [system_prompt] + user_context[user_id]

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_to_send,
            temperature=0.7
        )
        
        bot_response = completion.choices[0].message.content
        user_context[user_id].append({"role": "assistant", "content": bot_response})
        
        await message.answer(bot_response)
        
    except Exception as e:
        logger.error(f"Ошибка вызова Groq API: {e}")
        await message.answer(f"⚠️ Ошибка ИИ: `{str(e)}`")

async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
