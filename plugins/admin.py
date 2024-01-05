import pyromod
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from main import config
from constants.keyboards import ADMIN_OPTIONS
from models.users import User

admin_id = int(config.admin_id)

@Client.on_message(filters.user(admin_id))
async def admin_command(client: Client, message: Message):
    await client.send_message(
        chat_id=admin_id,
        text='Hello admin:',
        reply_markup=ADMIN_OPTIONS
    )


@Client.on_callback_query(filters.user(admin_id))
async def admin_callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    if data == 'bot_users':
        bot_users = User.select().count()
        await query.answer(f"Total users: {bot_users}", show_alert=True)
    elif data == 'public_message':
        await send_message_to_all_users(client)
        await query.answer("✅ Message sent to users.", show_alert=True)
    elif data == 'private_message':
        await send_message_to_specific_user(client)
        await query.answer("✅ message sent.", show_alert=True)


async def send_message_to_all_users(client: Client):
    users = User.select()
    msg = await client.ask(chat_id=admin_id, text="Send your message.")

    for user in users:
        user_id = user.chat_id
        if user_id == str(admin_id):
            continue
        await client.send_message(chat_id=user_id, text=msg.text)

async def send_message_to_specific_user(client: Client):
    user_id = await client.ask(chat_id=admin_id, text="send user id: ")
    msg = await client.ask(chat_id=admin_id, text="Now send your message.")

    await client.send_message(chat_id=user_id.text, text=msg.text)