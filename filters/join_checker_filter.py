from pyrogram import Client, filters
from pyrogram.types import Message
from constants.keyboards import JOIN_TO_CHANNEL_KEYBOARD
from constants.bot_messages import PLEASE_JOIN_TO_CHANNEL, TAKBAND_QANDEEL, MEMBER_STATUS_LIST

async def is_user_joined(_, client: Client, message: Message):
    chat_id = message.chat.id
    try:
        user = await client.get_chat_member(
            chat_id=TAKBAND_QANDEEL,
            user_id=chat_id,
        )
        if user.status == MEMBER_STATUS_LIST[0] or user.status == MEMBER_STATUS_LIST[1]:
            return False
        else:
            return True
    except Exception as e:
        await client.send_message(
            chat_id=chat_id,
            text=PLEASE_JOIN_TO_CHANNEL,
            reply_markup=JOIN_TO_CHANNEL_KEYBOARD
        )
        return False
    
is_joined_filter = filters.create(is_user_joined)