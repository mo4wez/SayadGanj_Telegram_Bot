from pyrogram import Client, filters
from pyrogram.types import Message
from constants.bot_messages import WELCOME_MESSAGE
from constants.join_checker_filter import is_joined_filter
from models.users import User
from time import sleep

@Client.on_message(filters.command('start') & is_joined_filter)
async def start(client: Client, message: Message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    username = message.from_user.username

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
    await message.reply_text(WELCOME_MESSAGE + ' ' + first_name)