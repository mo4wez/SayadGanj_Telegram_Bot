from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from main import config
from constants.keyboards import ADMIN_OPTIONS, CANCEL_KEYBOARD
from models.users import User
from constants.bot_messages import (
    WELCOME_ADMIN,
    PUBLIC_MESSAGE,
    PRIVATE_MESSAGE,
    BOT_USERS_CD,
    TOTAL_USERS,
    SEND_YOUR_MESSAGE,
    SEND_USER_ID,
    NOW_SEND_YOUR_MESSAGE,
    EXIT_BUTTON_DATA,
    EXITED_FROM_ADMIN,
    CANCEL,
    OPERATION_CANCELED,
    )

admin_id = int(config.admin_id)

@Client.on_message(filters.command('admin') & filters.user(admin_id))
async def admin_command(client: Client, message: Message):
    global admin_message
    admin_message = await client.send_message(
        chat_id=admin_id,
        text=WELCOME_ADMIN,
        reply_markup=ADMIN_OPTIONS
    )

@Client.on_callback_query()
async def admin_callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    if data == BOT_USERS_CD:
        bot_users = User.select().count()
        await query.answer(TOTAL_USERS.format(bot_users), show_alert=True)
    elif data == PUBLIC_MESSAGE:
        await send_message_to_all_users(client)
    elif data == PRIVATE_MESSAGE:
        await send_message_to_specific_user(client)
    elif data == EXIT_BUTTON_DATA:
        await query.edit_message_text(text=EXITED_FROM_ADMIN)
        return

async def send_message_to_all_users(client: Client):
    users = User.select()
    msg = await client.ask(chat_id=admin_id, text=SEND_YOUR_MESSAGE, reply_markup=CANCEL_KEYBOARD)

    if msg.text == CANCEL:
        await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
        return
    
    for user in users:
        user_id = user.chat_id
        if user_id == str(admin_id):
            continue
        await client.send_message(chat_id=user_id, text=msg.text)
    await client.send_message(chat_id=admin_id, text='Message sent to users.', reply_markup=ReplyKeyboardRemove())

async def send_message_to_specific_user(client: Client):
    while True:
        user_id_input = await client.ask(chat_id=admin_id, text=SEND_USER_ID, reply_markup=CANCEL_KEYBOARD)
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            break

        if not user_id.isdigit():
            await client.send_message(chat_id=admin_id, text="Please enter a user ID containing only digits. Try again.")
            continue  # Restart the loop to prompt for a valid user ID

        user = User.get_or_none(User.chat_id == int(user_id))
        if not user:
            await client.send_message(chat_id=admin_id, text="Wrong user ID! Please try another one.")
            continue  # Restart the loop to prompt for an existing user ID

        msg_input = await client.ask(chat_id=admin_id, text=NOW_SEND_YOUR_MESSAGE, reply_markup=CANCEL_KEYBOARD)
        msg = msg_input.text.strip()  # Trim leading/trailing spaces
    
        if msg == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            break

        await client.send_message(chat_id=user_id, text=msg)
        await client.send_message(chat_id=admin_id, text='Message sent to user.', reply_markup=ReplyKeyboardRemove())
        break
