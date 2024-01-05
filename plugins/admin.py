import pyromod
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from main import config
from constants.keyboards import ADMIN_OPTIONS
from models.users import User
from constants.bot_messages import (
    WELCOME_ADMIN,
    PRIVATE_MESSAGE_SENT,
    PUBLIC_MESSAGE_SENT,
    PUBLIC_MESSAGE,
    PRIVATE_MESSAGE,
    BOT_USERS_CD,
    TOTAL_USERS,
    SEND_YOUR_MESSAGE,
    SEND_USER_ID,
    NOW_SEND_YOUR_MESSAGE,
    USER_MODE_CD,
    USER_MODE_ACTIVATED
    )

admin_id = int(config.admin_id)

@Client.on_message(filters.user(admin_id))
async def admin_command(client: Client, message: Message):
    await client.send_message(
        chat_id=admin_id,
        text=WELCOME_ADMIN,
        reply_markup=ADMIN_OPTIONS
    )


@Client.on_callback_query(filters.user(admin_id))
async def admin_callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    if data == BOT_USERS_CD:
        bot_users = User.select().count()
        await query.answer(TOTAL_USERS.format(bot_users), show_alert=True)
    elif data == PUBLIC_MESSAGE:
        await send_message_to_all_users(client)
        await query.answer(PUBLIC_MESSAGE_SENT, show_alert=True)
    elif data == PRIVATE_MESSAGE:
        await send_message_to_specific_user(client)
        await query.answer(PRIVATE_MESSAGE_SENT, show_alert=True)
    elif data == USER_MODE_CD:
        await client.send_message(chat_id=admin_id, text=USER_MODE_ACTIVATED)
        return


async def send_message_to_all_users(client: Client):
    users = User.select()
    msg = await client.ask(chat_id=admin_id, text=SEND_YOUR_MESSAGE)

    for user in users:
        user_id = user.chat_id
        if user_id == str(admin_id):
            continue
        await client.send_message(chat_id=user_id, text=msg.text)

async def send_message_to_specific_user(client: Client):
    user_id = await client.ask(chat_id=admin_id, text=SEND_USER_ID)
    msg = await client.ask(chat_id=admin_id, text=NOW_SEND_YOUR_MESSAGE)

    await client.send_message(chat_id=user_id.text, text=msg.text)