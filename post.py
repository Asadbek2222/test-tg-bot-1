from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions
from datetime import datetime, timedelta
import asyncio

TOKEN = "8915545889:AAE4izMkcf1Je2rQXvx0SoxiZ8d1kAhcBNc"

OWNER_USERNAME = "CreeperBc"
OWNER_ID = 1464204023  # ВПИШИ СВОЙ ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

moderators = {}

def is_owner(user):
    return user.id == OWNER_ID or (user.username and user.username.lower() == OWNER_USERNAME.lower())


@dp.message()
async def handler(message: Message):

    if not message.text:
        return

    text = message.text.lower()

    # =====================
    # GIVE MOD
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
            limit = int(parts[1])

        target = message.reply_to_message.from_user

        moderators.setdefault(message.chat.id, {})
        moderators[message.chat.id][target.id] = {
            "level": levels[cmd],
            "limit": limit
        }

        await message.answer(f"✅ {target.full_name} модер {levels[cmd]} уровня\n⏳ лимит: {limit} минут")
        return

    # =====================
    # MUTE
    # =====================
    if text.startswith("мут"):

        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user
        sender = message.from_user

        # ❌ ЗАЩИТА ВЛАДЕЛЬЦА
        if is_owner(target):
            await message.answer("❌ Доступ запрещён: этого пользователя нельзя мутить")
            return

        if message.chat.id not in moderators:
            return

        if sender.id not in moderators[message.chat.id] and not is_owner(sender):
            return

        parts = text.split()
        if len(parts) < 2:
            return

        minutes = int(parts[1])

        sender_data = moderators[message.chat.id].get(sender.id, {"limit": 9999})

        if minutes > sender_data["limit"] and not is_owner(sender):
            await message.answer("❌ лимит превышен")
            return

        until = datetime.now() + timedelta(minutes=minutes)

        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )

        await message.answer(f"🔇 {target.full_name} мут на {minutes} мин")
        return


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())