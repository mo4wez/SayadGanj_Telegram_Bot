import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from main import config
from constants.keyboards import ADMIN_OPTIONS, CANCEL_KEYBOARD, ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
from models.users import User
from time import sleep
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
    NEW_POST_CALLBACK_TEXT,
    VIEW_POST_KEYBOARD_TEXT,
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
    elif data == NEW_POST_CALLBACK_TEXT:
        await send_new_post_notification(client)
    elif data == EXIT_BUTTON_DATA:
        await query.edit_message_text(text=EXITED_FROM_ADMIN)
        return

async def send_message_to_all_users(client: Client):
    users = User.select()
    msg = await client.ask(chat_id=admin_id, text=SEND_YOUR_MESSAGE, reply_markup=CANCEL_KEYBOARD)

    if msg.text == CANCEL:
        await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
        return
    
    blocked_users = []
    deactivated_users = []

    try:
        for user in users:
            user_id = user.chat_id
            username = user.username
            if user_id == str(admin_id):
                continue
            try:
                await client.send_message(chat_id=user_id, text=msg.text)
                await asyncio.sleep(0.5)  # Use asyncio.sleep instead of sleep
            except Exception as e:
                error_message = str(e)
                if 'PEER_ID_INVALID' in error_message:
                    # Handle the case where the user ID is invalid
                    continue
                elif 'USER_IS_BLOCKED' in error_message:
                    blocked_users.append((username, user_id))
                elif 'INPUT_USER_DEACTIVATED' in error_message:
                    deactivated_users.append((username, user_id))
                else:
                    # Log or handle other exceptions
                    await client.send_message(chat_id=admin_id, text=f'Error: {e}', reply_markup=ReplyKeyboardRemove())
        
        if blocked_users or deactivated_users:
            blocked_msg = "Blocked users:\n" + "\n".join([f"Username: {username}, Chat ID: {user_id}" for username, user_id in blocked_users])
            deactivated_msg = "Deactivated users:\n" + "\n".join([f"Username: {username}, Chat ID: {user_id}" for username, user_id in deactivated_users])
            final_msg = blocked_msg + "\n\n" + deactivated_msg
            await client.send_message(chat_id=admin_id, text=final_msg, reply_markup=ReplyKeyboardRemove())
        else:
            await client.send_message(chat_id=admin_id, text='Message sent to users. No users blocked the bot or were deactivated.', reply_markup=ReplyKeyboardRemove())
    
    except Exception as e:
        await client.send_message(chat_id=admin_id, text=f'Error: {e}', reply_markup=ReplyKeyboardRemove())

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

async def send_new_post_notification(client: Client):
    while True:
        msg = await client.ask(chat_id=admin_id, text='send your message:', reply_markup=CANCEL_KEYBOARD)

        if msg.text == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            return
        
        if not msg.text:
            await client.send_message(chat_id=admin_id, text='send only text.')
            continue
        
        while True:
            reply_markup_url = await client.ask(
                chat_id=admin_id,
                text='Send post link:'
            )
            if reply_markup_url.text == CANCEL:
                await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return

            if not re.match(r'^(http|https)://', reply_markup_url.text):
                await client.send_message(chat_id=admin_id, text="Invalid URL! Please send a valid link.", reply_markup=ReplyKeyboardRemove())
                continue

            notification_keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text=VIEW_POST_KEYBOARD_TEXT, url=reply_markup_url.text)]
                ]
                )

            post_sends_where = await client.ask(
                chat_id=admin_id,
                text='Where do you want to notification message should be send?',
                reply_markup=ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
            )

            if post_sends_where.text == CANCEL:
                await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return
            
            if post_sends_where.text == '👥 To users':
                users = User.select()
                if users:
                    for user in users:
                        user_id = user.chat_id
                        if user_id == str(admin_id):
                            continue
                        await client.send_message(chat_id=user_id, text=msg.text, reply_markup=notification_keyboard)
                    await client.send_message(chat_id=admin_id, text='Message sent to all users.', reply_markup=ReplyKeyboardRemove())
                    break
                else:
                    await client.send_message(chat_id=admin_id, text='No users start the bot yet...', reply_markup=ReplyKeyboardRemove())
                    break
            elif post_sends_where.text == '📢 To channel':
                await client.send_message(chat_id='takband_kandeel', text=msg.text, reply_markup=notification_keyboard)
                await client.send_message(chat_id=admin_id, text='Message sent to channel.', reply_markup=ReplyKeyboardRemove())
                break
            else:
                await client.send_message(chat_id=admin_id, text='Invalid selection, try again!', reply_markup=ReplyKeyboardRemove())
                continue
        break
    