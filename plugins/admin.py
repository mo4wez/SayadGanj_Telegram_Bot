import re
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from main import config
from constants.keyboards import ADMIN_OPTIONS, CANCEL_KEYBOARD, ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
from models.users import User, SearchHistory
from peewee import fn
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
    BALOCHBIT,
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
    SHOW_SEARCHER_CALLBACK_TEXT,
    )

SEARCHES_PER_PAGE = 10

admin_id = int(config.admin_id)

@Client.on_message(filters.command('admin') & filters.user(admin_id))
async def admin_command(client: Client, message: Message):
    global admin_message
    global admin_command_id
    admin_command_id = message.id

    admin_message = await client.send_message(
        chat_id=admin_id,
        text=WELCOME_ADMIN,
        reply_markup=ADMIN_OPTIONS
    )

@Client.on_callback_query(filters.user(admin_id), group=2)
async def admin_callback_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == BOT_USERS_CD:
        bot_users = User.select().count()
        await query.answer(TOTAL_USERS.format(bot_users), show_alert=True)
    elif data == "see_users":
        await show_bot_users(client)
    elif data == PUBLIC_MESSAGE:
        await send_message_to_all_users(client)
    elif data == PRIVATE_MESSAGE:
        await send_message_to_specific_user(client)
    elif data == NEW_POST_CALLBACK_TEXT:
        await send_new_post_notification(client)
    elif data == SHOW_SEARCHER_CALLBACK_TEXT:
        await show_users_searches(client)
    elif data == 'delete_user_searches':
        await delete_users_searches(client)
    elif data == EXIT_BUTTON_DATA:
        await query.answer(text=EXITED_FROM_ADMIN, show_alert=True)
        await client.delete_messages(chat_id=admin_id, message_ids=admin_message.id)
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

async def show_bot_users(client: Client):
    users = User.select()

    await display_bot_users(client, admin_id, users, page=1)

async def send_message_to_specific_user(client: Client):
    while True:
        user_id_input = await client.ask(chat_id=admin_id, text=SEND_USER_ID, reply_markup=CANCEL_KEYBOARD)
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            break

        # Check if input is numeric or a username
        if user_id.isdigit():
            # Treat input as chat_id
            user = User.get_or_none(User.chat_id == int(user_id))
        else:
            # Treat input as username (case-insensitive)
            user = User.get_or_none(fn.Lower(User.username) == user_id.lower())

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
                await client.send_message(chat_id=BALOCHBIT, text=msg.text, reply_markup=notification_keyboard)
                await client.send_message(chat_id=admin_id, text=MESSAGE_SENT_TO_CHANNEL_TEXT, reply_markup=ReplyKeyboardRemove())
                break
            else:
                await client.send_message(chat_id=admin_id, text=INVALID_SELECTION_TEXT, reply_markup=ReplyKeyboardRemove())
                continue
        break

async def show_users_searches(client: Client):
    while True:
        user_id_input = await client.ask(chat_id=admin_id, text=SEND_USER_ID, reply_markup=CANCEL_KEYBOARD)
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(chat_id=admin_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            break

        # Check if input is numeric or a username
        if user_id.isdigit():
            # Treat input as chat_id
            user = User.get_or_none(User.chat_id == int(user_id))
        else:
            # Treat input as username (case-insensitive)
            user = User.get_or_none(fn.Lower(User.username) == user_id.lower())

        if not user:
            await client.send_message(chat_id=admin_id, text=WRONG_USER_ID, reply_markup=ReplyKeyboardRemove())
            continue  # Restart the loop to prompt for an existing user ID
        
        user_searches = SearchHistory.select().where(SearchHistory.user == user).order_by(SearchHistory.search_date.desc())

        if not user_searches.exists():
            await client.send_message(chat_id=admin_id, text="No search history found for this user.", reply_markup=ReplyKeyboardRemove())
            continue

        # Display the first page of results
        await display_searches_page(client, admin_id, user, user_searches, page=1)
        break

async def display_searches_page(client, chat_id, user, searches, page, edit=False):
    total_searches = searches.count()
    total_pages = (total_searches + SEARCHES_PER_PAGE - 1) // SEARCHES_PER_PAGE
    start_index = (page - 1) * SEARCHES_PER_PAGE
    end_index = start_index + SEARCHES_PER_PAGE

    # Get searches for the current page
    searches_on_page = searches[start_index:end_index]

    formatted_searches = "\n".join(
        [f"{search.search_date}: {search.search_term}" for search in searches_on_page]
    )

    text = f"Search history for {user.first_name} (Page {page}/{total_pages}):\n\n{formatted_searches}"

    # Pagination buttons
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"searches_prev_{page - 1}_{user.chat_id}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"searches_next_{page + 1}_{user.chat_id}"))

    keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
    
    if not edit:
        global searches_message
        searches_message = await client.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
    if edit:
        await client.edit_message_text(chat_id=chat_id, message_id=searches_message.id, text=text, reply_markup=keyboard)

async def display_bot_users(client: Client, admin_id, users, page=1, edit=False):
    total_users = users.count()
    total_pages = (total_users + SEARCHES_PER_PAGE - 1) // SEARCHES_PER_PAGE
    start_index = (page - 1) * SEARCHES_PER_PAGE
    end_index = start_index + SEARCHES_PER_PAGE

    # Get searches for the current page
    users_on_page = users[start_index:end_index]
    

    formatted_users = "".join(
        [f"👤 user: {user.chat_id}\n\n- Name: {user.first_name}\n- Username: {'@' + user.username if user.username else user.username}\n- Joined at: {user.start_date}\n\n" for user in users_on_page]
    )

    text = f"Users list (Page {page}/{total_pages}):\n\n{formatted_users}"

    # Pagination buttons
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"users_prev_{page - 1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"users_next_{page + 1}"))

    keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
    
    if not edit:
        global users_message
        users_message = await client.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
    if edit:
        await client.edit_message_text(chat_id=admin_id, message_id=users_message.id, text=text, reply_markup=keyboard)

async def delete_users_searches(client: Client):
    while True:
        user_id_input = await client.ask(
            chat_id=admin_id,
            text=SEND_USER_ID,
            reply_markup=CANCEL_KEYBOARD
        )
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(
                chat_id=admin_id,
                text=OPERATION_CANCELED,
                reply_markup=ReplyKeyboardRemove()
            )
            break

        # Check if input is numeric or a username
        if user_id.isdigit():
            # Treat input as chat_id
            user = User.get_or_none(User.chat_id == int(user_id))
        else:
            # Treat input as username (case-insensitive)
            user = User.get_or_none(fn.Lower(User.username) == user_id.lower())

        if not user:
            await client.send_message(
                chat_id=admin_id,
                text=WRONG_USER_ID,
                reply_markup=ReplyKeyboardRemove()
            )
            continue  # Restart the loop to prompt for an existing user ID

        # Delete user's search history
        try:
            deleted_count = SearchHistory.delete().where(SearchHistory.user == user).execute()
            await client.send_message(
                chat_id=admin_id,
                text=f"Deleted {deleted_count} search(es) for user {user.first_name} ({user.chat_id})."
            )
            break
        except Exception as e:
            await client.send_message(chat_id=admin_id, text=f"An error occurred: {e}")
            break

@Client.on_callback_query(filters.user(admin_id), group=1)
async def handle_pagination_buttons(client: Client, query: CallbackQuery):
    data = query.data

    if data.startswith("searches_"):
        # Parse the callback data
        _, action, page, user_id = data.split("_")
        page = int(page)

        # Fetch user and searches again (from the original session or database)
        admin_id = query.message.chat.id  # Assuming the admin is using the bot
        user = User.get_or_none(User.chat_id == user_id)
        if not user:
            await query.answer("User not found!", show_alert=True)
            return

        searches = SearchHistory.select().where(SearchHistory.user == user).order_by(SearchHistory.search_date.desc())
        if not searches.exists():
            await query.answer("No searches found!", show_alert=True)
            return

        # Update the message with the new page
        await display_searches_page(client, admin_id, user, searches, page, edit=True)
        await query.answer()  # Acknowledge the callback query

@Client.on_callback_query(filters.user(admin_id), group=3)
async def handle_users_pagination_buttons(client: Client, query: CallbackQuery):
    data = query.data
    users = User.select()

    if data.startswith("users_"):
        # Parse the callback data
        _, action, page = data.split("_")
        page = int(page)

        # Update the message with the new page
        await display_bot_users(client, admin_id, users, page, edit=True)
        await query.answer()  # Acknowledge the callback query

