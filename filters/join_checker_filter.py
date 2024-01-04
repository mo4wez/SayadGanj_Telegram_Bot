from pyrogram import Client, filters
from pyrogram.types import Message
from constants.keyboards import JOIN_TO_CHANNEL_KEYBOARD
from constants.bot_messages import PLEASE_JOIN_TO_CHANNEL

async def is_user_joined(_, client: Client, message: Message):
    chat_id = message.chat.id
    try:
        user = await client.get_chat_member(
            chat_id="sayadganjjointest",
            user_id=message.chat.id,
        )
        if (not user.status == "left" or user.status == "kicked"):
            return True
    except Exception:
        await client.send_message(
            chat_id=chat_id,
            text=PLEASE_JOIN_TO_CHANNEL,
            reply_markup=JOIN_TO_CHANNEL_KEYBOARD
        )
        return False

is_joined_filter = filters.create(is_user_joined)