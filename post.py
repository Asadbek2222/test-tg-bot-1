from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

settings = {}
step = {}
temp_data = {}

@dp.message(Command("setup"))
async def setup(message: Message):

    if message.chat.type == "private":
        await message.answer("Команду нужно писать в группе")
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)

    if member.status not in ["administrator", "creator"]:
        await message.answer("Только админы могут настраивать")
        return

    step[message.from_user.id] = 1
    temp_data[message.from_user.id] = message.chat.id

    await message.answer("Отправь сообщение")

@dp.message(Command("stop"))
async def stop(message: Message):

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)

    if member.status not in ["administrator", "creator"]:
        return

    if message.chat.id in settings:
        del settings[message.chat.id]

    await message.answer("Остановлено")

@dp.message()
async def handler(message: Message):

    user_id = message.from_user.id

    if user_id not in step:
        return

    chat_id = temp_data[user_id]

    if step[user_id] == 1:

        settings[chat_id] = {
            "from_chat_id": message.chat.id,
            "message_id": message.message_id,
            "interval": 3600
        }

        step[user_id] = 2

        await message.answer("Теперь отправь время в секундах")
        return

    if step[user_id] == 2:

        try:
            settings[chat_id]["interval"] = int(message.text)
            await message.answer("Готово")
        except:
            await message.answer("Нужно число")

        del step[user_id]
        del temp_data[user_id]

async def sender():

    timers = {}

    while True:

        for chat_id in list(settings.keys()):

            if chat_id not in timers:
                timers[chat_id] = 0

            timers[chat_id] += 1

            if timers[chat_id] >= settings[chat_id]["interval"]:

                try:
                    await bot.forward_message(
                        chat_id,
                        settings[chat_id]["from_chat_id"],
                        settings[chat_id]["message_id"]
                    )
                except:
                    pass

                timers[chat_id] = 0

        await asyncio.sleep(1)

async def main():
    asyncio.create_task(sender())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())