from pyrogram import Client, filters
from pyrogram.types import Message

async def is_user_joined(_, client: Client, message: Message):
    try:
        user = await client.get_chat_member(
            chat_id="sayadganjjointest",
            user_id=message.chat.id,
        )
        return not user.status == "left" or user.status == "kicked"
    except Exception as e:
        await message.reply_text(
            f'Please join the channel. {e}'
        )

is_joined_filter = filters.create(is_user_joined)