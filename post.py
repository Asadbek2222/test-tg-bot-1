from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio

TOKEN = "8915545889:AAE4izMkcf1Je2rQXvx0SoxiZ8d1kAhcBNc"

OWNER_USERNAME = "CreeperBc"
OWNER_ID = 1464204023

bot = Bot(token=TOKEN)
dp = Dispatcher()

moderators = {}

# =========================
# АВТОПОСТ
# =========================
settings = {}
step = {}
temp_data = {}
last_posts = {}


def is_owner(user):
    return user.id == OWNER_ID or (
        user.username and user.username.lower() == OWNER_USERNAME.lower()
    )


def get_mod(chat_id, user_id):
    return moderators.get(chat_id, {}).get(user_id)


# =========================
# SETUP
# =========================
@dp.message(Command("setup"))
async def setup(message: Message):

    if not is_owner(message.from_user):
        return

    if message.chat.type == "private":
        await message.answer("❌ команду пиши в группе")
        return

    step[message.chat.id] = "wait_text"

    await message.answer(
        "📝 отправь текст для автопоста"
    )


# =========================
# STOP
# =========================
@dp.message(Command("stop"))
async def stop(message: Message):

    if not is_owner(message.from_user):
        return

    settings.pop(message.chat.id, None)

    # удалить последний пост
    if message.chat.id in last_posts:
        try:
            await bot.delete_message(
                message.chat.id,
                last_posts[message.chat.id]
            )
        except:
            pass

    await message.answer("🛑 автопост остановлен")


# =========================
# ОСНОВНОЙ ХЕНДЛЕР
# =========================
@dp.message()
async def handler(message: Message):

    if not message.text:
        return

    text = message.text.lower()

    # =========================
    # НАСТРОЙКА АВТОПОСТА
    # =========================
    if (
        message.chat.id in step
        and step[message.chat.id] == "wait_text"
    ):

        temp_data[message.chat.id] = {
            "text": message.text
        }

        step[message.chat.id] = "wait_time"

        await message.answer(
            "⏳ теперь отправь время в минутах"
        )
        return

    if (
        message.chat.id in step
        and step[message.chat.id] == "wait_time"
    ):

        try:
            minutes = int(message.text)
        except:
            await message.answer("❌ отправь число")
            return

        settings[message.chat.id] = {
            "text": temp_data[message.chat.id]["text"],
            "time": minutes
        }

        step.pop(message.chat.id)

        await message.answer(
            f"✅ автопост включён\n"
            f"⏳ каждые {minutes} минут"
        )
        return

    # =====================
    # БОТ
    # =====================
    if text.startswith("бот"):

        msg = message.text[4:]

        if not msg:
            return

        await message.reply(msg)
        return

    # =====================
    # МОДЕРЫ
    # =====================
    if text == "модеры":

        if message.chat.id not in moderators:
            await message.answer("❌ модеров нет")
            return

        mods = moderators[message.chat.id]

        if not mods:
            await message.answer("❌ модеров нет")
            return

        result = "👮 модеры:\n\n"

        for user_id, data in mods.items():

            try:
                member = await bot.get_chat_member(
                    message.chat.id,
                    user_id
                )

                name = member.user.full_name

            except:
                name = str(user_id)

            result += (
                f"• {name}\n"
                f"уровень: {data['level']}\n"
                f"лимит: {data['limit']} мин\n\n"
            )

        await message.answer(result)
        return

    # =====================
    # ВЫДАТЬ МОДЕРА
    # =====================
    if text.startswith("модер"):

        if not is_owner(message.from_user):
            return

        if not message.reply_to_message:
            return

        parts = text.split()
        cmd = parts[0]

        levels = {
            "модер1": 1,
            "модер2": 2,
            "модер3": 3
        }

        if cmd not in levels:
            return

        limit = 10

        if len(parts) > 1:
            try:
                limit = int(parts[1])
            except:
                return

        target = message.reply_to_message.from_user

        moderators.setdefault(message.chat.id, {})

        moderators[message.chat.id][target.id] = {
            "level": levels[cmd],
            "limit": limit
        }

        await message.answer(
            f"✅ {target.full_name} теперь модер {levels[cmd]} уровня\n"
            f"⏳ лимит мута: {limit} минут"
        )
        return

    # =====================
    # СНЯТЬ МОДЕРА
    # =====================
    if text == "снят":

        if not is_owner(message.from_user):
            return

        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user

        if message.chat.id in moderators:
            moderators[message.chat.id].pop(target.id, None)

        await message.answer(
            f"❌ {target.full_name} больше не модер"
        )
        return

    # =====================
    # МОЛЧАТЬ
    # =====================
    if text.startswith("молчать"):

        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user
        sender = message.from_user

        # защита овнера
        if is_owner(target):
            await message.answer(
                "❌ вы не можете мутить крипера так как он лучше а ты лох"
            )
            return

        if message.chat.id not in moderators:
            return

        if sender.id not in moderators[message.chat.id] and not is_owner(sender):
            return

        parts = text.split()

        if len(parts) < 2:
            return

        try:
            minutes = int(parts[1])
        except:
            return

        sender_data = get_mod(message.chat.id, sender.id)
        target_data = get_mod(message.chat.id, target.id)

        sender_level = sender_data["level"] if sender_data else 999
        target_level = target_data["level"] if target_data else 0

        # нельзя мутить равного или выше
        if (
            not is_owner(sender)
            and target_data
            and sender_level <= target_level
        ):
            await message.answer(
                "❌ нельзя мутить модера равного или выше ранга"
            )
            return

        sender_limit = sender_data["limit"] if sender_data else 9999

        if minutes > sender_limit and not is_owner(sender):
            await message.answer("❌ лимит превышен")
            return

        until = datetime.now() + timedelta(minutes=minutes)

        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target.id,
                permissions=ChatPermissions(
                    can_send_messages=False
                ),
                until_date=until
            )

            await message.answer(
                f"🔇 {target.full_name} получил мут на {minutes} мин"
            )

        except Exception as e:
            await message.answer(f"❌ ошибка мута: {e}")

        return

    # =====================
    # МОЖНО
    # =====================
    if text == "можно":

        if not message.reply_to_message:
            return

        sender = message.from_user
        target = message.reply_to_message.from_user

        if message.chat.id not in moderators:
            return

        if sender.id not in moderators[message.chat.id] and not is_owner(sender):
            return

        sender_data = get_mod(message.chat.id, sender.id)
        target_data = get_mod(message.chat.id, target.id)

        sender_level = sender_data["level"] if sender_data else 999
        target_level = target_data["level"] if target_data else 0

        # нельзя размучивать равного или выше
        if (
            not is_owner(sender)
            and target_data
            and sender_level <= target_level
        ):
            await message.answer(
                "❌ нельзя размучивать модера равного или выше ранга"
            )
            return

        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target.id,
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
                    can_invite_users=True
                )
            )

            await message.answer(
                f"✅ {target.full_name} теперь может говорить"
            )

        except Exception as e:
            await message.answer(f"❌ ошибка размута: {e}")

        return


# =========================
# АВТОПОСТ ЦИКЛ
# =========================
async def autopost_loop():

    while True:

        for chat_id, data in list(settings.items()):

            try:

                # удалить старый пост
                if chat_id in last_posts:

                    try:
                        await bot.delete_message(
                            chat_id,
                            last_posts[chat_id]
                        )
                    except:
                        pass

                msg = await bot.send_message(
                    chat_id,
                    data["text"]
                )

                last_posts[chat_id] = msg.message_id

            except:
                pass

        await asyncio.sleep(60 * data["time"])


# =========================
# MAIN
# =========================
async def main():

    asyncio.create_task(autopost_loop())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())