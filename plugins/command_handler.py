from pyrogram import Client, filters
from pyrogram.types import Message
from filters.join_checker_filter import is_user_joined
from models.users import User
from constants.bot_messages import WELCOME_MESSAGE, INLINE_SEARCH_BODY
from constants.keyboards import INLINE_SEARCH_BUTTON

from main import config

admin_id = int(config.admin_id)

@Client.on_message(filters.command('start'))
async def start(client: Client, message: Message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    if not await is_user_joined(None, client, message):
        return

    user = User.get_or_none(User.chat_id == chat_id)
    if user:
        user.first_name = first_name
        user.username = username
        user.save()
    else:
        User.create(
            chat_id=chat_id,
            first_name=first_name,
            username=username,
        )
    await message.reply_text(WELCOME_MESSAGE)

@Client.on_message(filters.command('search'))
async def search(client: Client, message: Message):
    chat_id = message.chat.id
    
    if not await is_user_joined(None, client, message):
        return
    
    await client.send_message(
        chat_id=chat_id,
        text=INLINE_SEARCH_BODY,
        reply_markup=INLINE_SEARCH_BUTTON
    )