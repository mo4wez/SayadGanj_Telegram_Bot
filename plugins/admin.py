import re
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from main import config
from constants.keyboards import ADMIN_OPTIONS, CANCEL_KEYBOARD, ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
from models.users import User
from constants.bot_messages import (
    WELCOME_ADMIN,
    PUBLIC_MESSAGE,
    PRIVATE_MESSAGE,
    BOT_USERS_CD,
    TOTAL_USERS,
    SEND_YOUR_MESSAGE,
    SEND_USER_ID,
    PRIVATE_MESSAGE_SENT,
    PUBLIC_MESSAGE_SENT,
    SEND_POST_MESSAGE,
    NOW_SEND_YOUR_MESSAGE,
    SEND_ONLY_TEXT,
    SEND_POST_LINK_TEXT,
    SEND_BUTTON_TEXT,
    WRONG_USER_ID,
    INVALID_POST_LINK,
    NOTIF_SENT_PLACE_TEXT,
    TO_USERS_TEXT,
    TO_CHANNEL_TEXT,
    NO_USERS_TEXT,
    TAKBAND_QANDEEL,
    MESSAGE_SENT_TO_CHANNEL_TEXT,
    INVALID_SELECTION_TEXT,
    ENTER_ID_INTEGER_ERROR,
    REPORT_FILE_CAPTION,
    EXIT_BUTTON_DATA,
    EXITED_FROM_ADMIN,
    CANCEL,
    OPERATION_CANCELED,
    NEW_POST_CALLBACK_TEXT,
    PEER_ID_INVALID,
    USER_IS_BLOCKED,
    INPUT_USER_DEACTIVATED,
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
        await query.answer(text=EXITED_FROM_ADMIN, show_alert=True)
        await client.delete_messages(
            chat_id=admin_id,
            message_ids=admin_message.id
        )
        return

async def send_message_to_all_users(client: Client):
    users = User.select()
    msg = await client.ask(chat_id=admin_id, text=SEND_YOUR_MESSAGE, reply_markup=CANCEL_KEYBOARD)

    if msg.text == CANCEL:
        await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
        return
    
    blocked_users = []
    deactivated_users = []
    invalid_users = []

    try:
        for user in users:
            user_id = user.chat_id
            username = user.username
            if user_id == str(admin_id):
                continue
            try:
                await client.send_message(chat_id=user_id, text=msg.text)
                await asyncio.sleep(0.2)
            except Exception as e:
                error_message = str(e)
                if PEER_ID_INVALID in error_message:
                    invalid_users.append((username, user_id))
                    User.delete().where(User.chat_id == user_id).execute()
                    continue
                elif USER_IS_BLOCKED in error_message:
                    blocked_users.append((username, user_id))
                    User.delete().where(User.chat_id == user_id).execute()
                    continue
                elif INPUT_USER_DEACTIVATED in error_message:
                    deactivated_users.append((username, user_id))
                    User.delete().where(User.chat_id == user_id).execute()
                    continue
                else:
                    await client.send_message(chat_id=admin_id, text=f'Error: {e}', reply_markup=ReplyKeyboardRemove())
        
        report_parts = []
        if blocked_users:
            blocked_msg = "Blocked users:\n" + "\n".join([f"Username: {username}, Chat ID: {user_id}" for username, user_id in blocked_users])
            report_parts.append(blocked_msg)
        if deactivated_users:
            deactivated_msg = "Deactivated users:\n" + "\n".join([f"Username: {username}, Chat ID: {user_id}" for username, user_id in deactivated_users])
            report_parts.append(deactivated_msg)
        if invalid_users:
            invalid_msg = "Invalid users:\n" + "\n".join([f"Username: {username}, Chat ID: {user_id}" for username, user_id in invalid_users])
            report_parts.append(invalid_msg)
        
        if report_parts:
            final_report = "\n\n".join(report_parts)
            file_path = os.path.join(os.getcwd(), 'user_report.txt')
            with open(file_path, 'w') as f:
                f.write(final_report)

            await client.send_document(chat_id=admin_id, document=file_path, caption=REPORT_FILE_CAPTION, reply_markup=ReplyKeyboardRemove())
            os.remove(file_path)
        else:
            await client.send_message(chat_id=admin_id, text=PUBLIC_MESSAGE_SENT, reply_markup=ReplyKeyboardRemove())
    
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
            await client.send_message(chat_id=admin_id, text=ENTER_ID_INTEGER_ERROR)
            continue  # Restart the loop to prompt for a valid user ID

        user = User.get_or_none(User.chat_id == int(user_id))
        if not user:
            await client.send_message(chat_id=admin_id, text=WRONG_USER_ID, reply_markup=ReplyKeyboardRemove())
            continue  # Restart the loop to prompt for an existing user ID

        msg_input = await client.ask(chat_id=admin_id, text=NOW_SEND_YOUR_MESSAGE, reply_markup=CANCEL_KEYBOARD)
        msg = msg_input.text.strip()  # Trim leading/trailing spaces
    
        if msg == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            break

        await client.send_message(chat_id=user_id, text=msg)
        await client.send_message(chat_id=admin_id, text=PRIVATE_MESSAGE_SENT, reply_markup=ReplyKeyboardRemove())
        break

async def send_new_post_notification(client: Client):
    while True:
        msg = await client.ask(chat_id=admin_id, text=SEND_POST_MESSAGE, reply_markup=CANCEL_KEYBOARD)

        if msg.text == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            return
        
        if not msg.text:
            await client.send_message(chat_id=admin_id, text=SEND_ONLY_TEXT)
            continue
        
        while True:
            reply_markup_url = await client.ask(
                chat_id=admin_id,
                text=SEND_POST_LINK_TEXT
            )
            if reply_markup_url.text == CANCEL:
                await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return

            if not re.match(r'^(http|https)://', reply_markup_url.text):
                await client.send_message(chat_id=admin_id, text=INVALID_POST_LINK, reply_markup=ReplyKeyboardRemove())
                continue

            view_post_button_text = await client.ask(
                chat_id=admin_id,
                text=SEND_BUTTON_TEXT
            )
            if view_post_button_text.text == CANCEL:
                await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return

            if not view_post_button_text.text:
                await client.send_message(chat_id=admin_id, text=SEND_ONLY_TEXT)
                continue

            notification_keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text=view_post_button_text.text, url=reply_markup_url.text)]
                ]
                )

            post_sends_where = await client.ask(
                chat_id=admin_id,
                text=NOTIF_SENT_PLACE_TEXT,
                reply_markup=ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
            )

            if post_sends_where.text == CANCEL:
                await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return
            
            if post_sends_where.text == TO_USERS_TEXT:
                users = User.select()
                if users:
                    for user in users:
                        user_id = user.chat_id
                        if user_id == str(admin_id):
                            continue
                        await client.send_message(chat_id=user_id, text=msg.text, reply_markup=notification_keyboard)
                    await client.send_message(chat_id=admin_id, text=PUBLIC_MESSAGE_SENT, reply_markup=ReplyKeyboardRemove())
                    break
                else:
                    await client.send_message(chat_id=admin_id, text=NO_USERS_TEXT, reply_markup=ReplyKeyboardRemove())
                    break
            elif post_sends_where.text == TO_CHANNEL_TEXT:
                await client.send_message(chat_id=TAKBAND_QANDEEL, text=msg.text, reply_markup=notification_keyboard)
                await client.send_message(chat_id=admin_id, text=MESSAGE_SENT_TO_CHANNEL_TEXT, reply_markup=ReplyKeyboardRemove())
                break
            else:
                await client.send_message(chat_id=admin_id, text=INVALID_SELECTION_TEXT, reply_markup=ReplyKeyboardRemove())
                continue
        break
