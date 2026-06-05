from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio
import os

TOKEN = os.getenv("8915545889:AAE4izMkcf1Je2rQXvx0SoxiZ8d1kAhcBNc")

OWNER_USERNAME = "CreeperBc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

settings = {}
step = {}
temp_data = {}

moderators = {}
unmute_tasks = {}

# =====================
# АВТОПОСТ
# =====================

@dp.message(Command("setup"))
async def setup(message: Message):

    if message.chat.type == "private":
        return

    if message.from_user.username != OWNER_USERNAME:
        return

    step[message.from_user.id] = 1
    temp_data[message.from_user.id] = message.chat.id

    await message.answer("Отправь сообщение для автопоста")

@dp.message(Command("stop"))
async def stop(message: Message):

    if message.from_user.username != OWNER_USERNAME:
        return

    if message.chat.id in settings:
        del settings[message.chat.id]

    await message.answer("Автопост остановлен")

# =====================
# НАСТРОЙКА АВТОПОСТА
# =====================

@dp.message()
async def setup_handler(message: Message):

    user_id = message.from_user.id

    if user_id not in step:
        return

    chat_id = temp_data[user_id]

    if step[user_id] == 1:

        settings[chat_id] = {
            "from_chat_id": message.chat.id,
            "message_id": message.message_id,
            "interval": 3600,
            "last_message_id": None
        }

        step[user_id] = 2

        await message.answer("Отправь время в секундах")
        return

    if step[user_id] == 2:

        try:

            settings[chat_id]["interval"] = int(message.text)

            await message.answer("✅ Автопост настроен")

        except:
            await message.answer("Нужно отправить число")

        del step[user_id]
        del temp_data[user_id]

# =====================
# ВЫДАЧА МОДЕРА
# =====================

@dp.message()
async def mod_system(message: Message):

    if message.chat.type == "private":
        return

    if not message.reply_to_message:
        return

    if message.from_user.username != OWNER_USERNAME:
        return

    args = message.text.lower().split()

    if len(args) < 1:
        return

    cmd = args[0]


    levels = {
        "модер1": 1,
        "модер2": 2,
        "модер3": 3
    }

    if cmd not in levels:
        return

    target = message.reply_to_message.from_user

    max_mute = 10

    if len(args) >= 2:
        try:
            max_mute = int(args[1])
        except:
            return

    if message.chat.id not in moderators:
        moderators[message.chat.id] = {}

    moderators[message.chat.id][target.id] = {
        "level": levels[cmd],
        "max_mute": max_mute
    }

    await message.answer(
        f"✅ {target.full_name} теперь модер {levels[cmd]} уровня\n"
        f"⏳ Максимальный мут: {max_mute} минут"
    )

# =====================
# СНЯТИЕ МУТА
# =====================

async def unmute_user(chat_id, user_id, minutes):

    await asyncio.sleep(minutes * 60)

    try:

        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )

        user = await bot.get_chat_member(chat_id, user_id)

        await bot.send_message(
            chat_id,
            f"✅ {user.user.full_name} вышел с мута"
        )

    except:
        pass

# =====================
# МУТ
# =====================

@dp.message()
async def mute_system(message: Message):

    if message.chat.type == "private":
        return

    if not message.reply_to_message:
        return

    if not message.text.lower().startswith("мут"):
        return

    if message.chat.id not in moderators:
        return

    sender_id = message.from_user.id

    if sender_id not in moderators[message.chat.id]:
        return

    sender_data = moderators[message.chat.id][sender_id]

    target = message.reply_to_message.from_user
    target_id = target.id

    args = message.text.split()

    if len(args) < 2:
        return

    try:
        mute_minutes = int(args[1])
    except:
        return

    if mute_minutes > sender_data["max_mute"]:

        await message.answer(
            "❌ Ты не можешь дать такой долгий мут"
        )
        return

    if target.username == OWNER_USERNAME:

        await message.answer(
            "❌ Вы не можете дать мут Криперу\n\n"
            "Причина: ты лох а он лучше 😎"
        )
        return

    target_level = 0

    if target_id in moderators[message.chat.id]:
        target_level = moderators[message.chat.id][target_id]["level"]

    if target_level >= sender_data["level"]:

        await message.answer(
            "❌ Нельзя мутить модератора выше или равного уровня"
        )
        return

    until_date = datetime.now() + timedelta(minutes=mute_minutes)

    try:

        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )

        await message.answer(
            f"🔇 {target.full_name} получил мут на {mute_minutes} минут"
        )

        task = asyncio.create_task(
            unmute_user(
                message.chat.id,
                target_id,
                mute_minutes
            )
        )

        unmute_tasks[target_id] = task

    except:

        await message.answer("Ошибка мута")

# =====================
# АВТОПОСТ ЦИКЛ
# =====================

async def sender():

    timers = {}

    while True:

        for chat_id in list(settings.keys()):

            if chat_id not in timers:
                timers[chat_id] = 0

            timers[chat_id] += 1

            if timers[chat_id] >= settings[chat_id]["interval"]:

                try:

                    old_message_id = settings[chat_id]["last_message_id"]

                    if old_message_id:

                        try:
                            await bot.delete_message(
                                chat_id,
                                old_message_id
                            )
                        except:
                            pass

                    sent = await bot.forward_message(
                        chat_id,
                        settings[chat_id]["from_chat_id"],
                        settings[chat_id]["message_id"]
                    )

                    settings[chat_id]["last_message_id"] = sent.message_id

                except:
                    pass

                timers[chat_id] = 0

        await asyncio.sleep(1)

# =====================
# MAIN
# =====================

async def main():

    asyncio.create_task(sender())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())