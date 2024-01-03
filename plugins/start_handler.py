from pyrogram import Client, filters
from pyrogram.types import Message
from constants.bot_messages import WELCOME_MESSAGE


@Client.on_message(filters.command('start'))
async def start(client: Client, message: Message):
    await message.reply_text(WELCOME_MESSAGE)