import re
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.raw.base import reply_markup
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from main import config
from constants.keyboards import ADMIN_OPTIONS, CANCEL_KEYBOARD, ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
from models.users import User, SearchHistory
from models.admins import Admin
from peewee import fn
from constants.bot_messages import *
from filters.join_checker_filter import load_channel_settings, save_channel_settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

SEARCHES_PER_PAGE = 10

# Get the owner ID from config
owner_id = int(config.admin_id)

# Define admin_states dictionary for channel settings
admin_states = {}

# Initialize Admin table and ensure owner is in the database
def initialize_admin_table():
    try:
        # Create the table if it doesn't exist
        Admin.create_table(safe=True)
        
        # Check if owner exists in the admin table
        owner = Admin.get_or_none(Admin.chat_id == owner_id)
        if not owner:
            # Add owner to the admin table
            owner_user = User.get_or_none(User.chat_id == owner_id)
            if owner_user:
                Admin.create(
                    chat_id=owner_id,
                    username=owner_user.username,
                    first_name=owner_user.first_name,
                    added_by=owner_id,
                    is_owner=True
                )
            else:
                # If owner is not in the users table, create with minimal info
                Admin.create(
                    chat_id=owner_id,
                    username="owner",
                    first_name="Owner",
                    added_by=owner_id,
                    is_owner=True
                )
        elif not owner.is_owner:
            # Ensure the owner has is_owner flag set to True
            owner.is_owner = True
            owner.save()
    except Exception as e:
        logger.error(f"Error initializing admin table: {e}")

# Call the initialization function
initialize_admin_table()

# Helper function to check if a user is an admin
def is_admin(user_id):
    try:
        # First check if the user is the owner from config
        if str(user_id) == str(owner_id):
            return True
            
        # Then check the database if it's available
        try:
            admin = Admin.get_or_none(Admin.chat_id == user_id)
            return admin is not None
        except Exception as e:
            logger.error(f"Error checking admin status in database: {e}")
            # If database check fails, fall back to owner check only
            return str(user_id) == str(owner_id)
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        # If all checks fail, default to owner ID only
        return str(user_id) == str(owner_id)

# Helper function to check if a user is the owner
def is_owner(user_id):
    try:
        # First check against config owner_id
        if str(user_id) == str(owner_id):
            return True
            
        # Then check database if available
        try:
            admin = Admin.get_or_none(Admin.chat_id == user_id, Admin.is_owner == True)
            return admin is not None
        except Exception as e:
            logger.error(f"Error checking owner status in database: {e}")
            # If database check fails, fall back to owner check only
            return str(user_id) == str(owner_id)
    except Exception as e:
        logger.error(f"Error checking owner status: {e}")
        # If all checks fail, default to owner ID only
        return str(user_id) == str(owner_id)

# Create a filter for admin users
admin_filter = filters.create(lambda _, __, message: is_admin(message.from_user.id))
owner_filter = filters.create(lambda _, __, message: is_owner(message.from_user.id))

admin_messages = {}
admin_command_id = None

@Client.on_message(filters.command('admin') & admin_filter, group=0)
async def admin_command(client: Client, message: Message):
    global admin_command_id
    admin_command_id = message.id

    # Check if the user is the owner to show additional options
    is_user_owner = is_owner(message.from_user.id)
    
    # Use the appropriate keyboard based on user's role
    keyboard = ADMIN_OPTIONS
    
    # If the user is the owner, add the "Add Admin" button
    if is_user_owner:
        # Create a copy of the keyboard to avoid modifying the original
        keyboard_rows = [row.copy() for row in ADMIN_OPTIONS.inline_keyboard]
        
        # Add the "Add Admin" button
        keyboard_rows.append([InlineKeyboardButton(ADD_ADMIN, callback_data=ADD_ADMIN_CD)])

        # add "remove admin" button
        keyboard_rows.append([InlineKeyboardButton(REMOVE_ADMIN, callback_data=REMOVE_ADMIN_CD)])
        
        # Create a new keyboard with the additional button
        keyboard = InlineKeyboardMarkup(keyboard_rows)

    admin_messages[message.chat.id] = await client.send_message(
        chat_id=message.chat.id,
        text=WELCOME_ADMIN,
        reply_markup=keyboard
    )

@Client.on_callback_query(admin_filter, group=20)
async def admin_callback_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == BOT_USERS_CD:
        bot_users = User.select().count()
        await query.answer(TOTAL_USERS.format(bot_users), show_alert=True)
    elif data == SEE_BOT_USERS_CD:
        await show_bot_users(client, query)
    elif data == PUBLIC_MESSAGE:
        await send_message_to_all_users(client, query)
    elif data == PRIVATE_MESSAGE:
        await send_message_to_specific_user(client, query)
    elif data == NEW_POST_CALLBACK_TEXT:
        await send_new_post_notification(client, query)
    elif data == SHOW_SEARCHER_CALLBACK_TEXT:
        await show_users_searches(client, query)
    elif data == DELETE_USER_SEARCHES_CD:
        await delete_users_searches(client, query)
    elif data == ADMIN_WOD_SETTINGS_CD:
        from plugins.word_of_day import word_of_day_settings

        admin_msg = admin_messages.get(query.message.chat.id)

        if admin_msg:
            await client.delete_messages(chat_id=query.message.chat.id, message_ids=admin_msg.id)
        # Directly call the word_of_day_settings function
        # Create a dummy message object to pass to the function
        dummy_message = Message(
            id=0,
            chat=query.message.chat,
            from_user=query.from_user,
            text="/word_of_day_settings",
            client=client
        )
        await word_of_day_settings(client, dummy_message)
    elif data == ADMIN_SEND_WOD_CD:
        from plugins.word_of_day import send_word_of_day

        admin_msg = admin_messages.get(query.message.chat.id)
        if admin_msg:
            await client.delete_messages(chat_id=query.message.chat.id, message_ids=admin_msg.id)
        # First send a confirmation message
        confirmation = await client.send_message(
            chat_id=query.message.chat.id,
            text=SENING_WORD_THE_DAY_TO_ALL_USERS
        )
        # Then call the function to send word of day
        await send_word_of_day(client)
    elif data == CHANNEL_SETTINGS_CD:
        dummy_message = Message(
            id=1,
            chat=query.message.chat,
            from_user=query.from_user,
            text="/channel_settings",
            client=client
        )
        await channel_settings_command(client, dummy_message)
    elif data == ADD_ADMIN_CD and is_owner(query.from_user.id):
        # Only the owner can add admins
        await add_admin(client, query.message.chat.id)
    elif data == REMOVE_ADMIN_CD and is_owner(query.from_user.id):
        await remove_admin(client, query.message.chat.id)
    elif data == EXIT_BUTTON_DATA:
        await query.answer(text=EXITED_FROM_ADMIN, show_alert=True)
        admin_msg = admin_messages.get(query.message.chat.id)
        if admin_msg:
            try:
                await client.delete_messages(chat_id=query.message.chat.id, message_ids=admin_msg.id)
                del admin_messages[query.message.chat.id]
            except Exception as e:
                logger.error(f"Error deleting admin message: {e}")
        return

# Function to add a new admin
async def add_admin(client, chat_id):
    while True:
        user_id_input = await client.ask(
            chat_id=chat_id, 
            text=PLEASE_SEND_PERSON_ID_OR_USERNAME_YOU_WANT_TO_BE_ADMIN,
            reply_markup=CANCEL_KEYBOARD
        )
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(
                chat_id=chat_id,
                text=OPERATION_CANCELED,
                reply_markup=ReplyKeyboardRemove()
            )
            break

        # Check if input is numeric or a username
        if user_id.isdigit():
            # Treat input as chat_id
            user = User.get_or_none(User.chat_id == int(user_id))
            user_chat_id = int(user_id)
        else:
            # Treat input as username (case-insensitive)
            user = User.get_or_none(fn.Lower(User.username) == user_id.lower())
            if user:
                user_chat_id = user.chat_id
            else:
                user_chat_id = None

        if not user:
            await client.send_message(
                chat_id=chat_id,
                text=USER_NOT_INTERACTED_NOT_FOUND,
                reply_markup=ReplyKeyboardRemove()
            )
            continue  # Restart the loop to prompt for an existing user ID

        # Check if user is already an admin
        existing_admin = Admin.get_or_none(Admin.chat_id == user_chat_id)
        if existing_admin:
            await client.send_message(
                chat_id=chat_id,
                text=USER_X_ALREADY_AN_ADMIN.format(user.first_name),
                reply_markup=ReplyKeyboardRemove()
            )
            break

        # Add user as admin
        try:
            Admin.create(
                chat_id=user_chat_id,
                username=user.username,
                first_name=user.first_name,
                added_by=chat_id,
                is_owner=False  # Only the original admin is the owner
            )
            
            await client.send_message(
                chat_id=chat_id,
                text=USER_X_HAS_BEEN_ADDED_AS_AN_ADMIN.format(user.first_name),
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Notify the new admin
            try:
                await client.send_message(
                    chat_id=user_chat_id,
                    text=YOU_HAVE_BEEN_ADED_AS_ADMIN
                )
            except Exception as e:
                logger.error(f"Failed to notify new admin: {e}")
            
            break
        except Exception as e:
            await client.send_message(
                chat_id=chat_id,
                text=ERROR_WHILE_ADDING_THE_ADMIN.format(e),
                reply_markup=ReplyKeyboardRemove()
            )
            break

async def remove_admin(client, chat_id):
    """Function to remove an admin"""

    admins = Admin.select().where(Admin.is_owner == False)

    if not admins.exists():
        await client.send_message(
            chat_id=chat_id,
            text=NO_ADMINS_TO_REMOVE
        )
        return

    keyboard = []
    for admin in admins:
        display_name = admin.first_name
        if admin.username:
            display_name += f" (@{admin.username})"
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"remove_admin_{admin.chat_id}")])

    keyboard.append([InlineKeyboardButton(CANCEL, callback_data="cancel_admin_removal")])

    await client.send_message(
        chat_id=chat_id,
        text=SELECT_ADMIN_TO_REMOVE,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex(r"^remove_admin_(\d+)$") & owner_filter, group=21)
async def remove_admin_callback(client: Client, query: CallbackQuery):
    """Handle admin removal confirmation"""
    admin_id = query.data.split("_")[2]

    try:
        admin = Admin.get(Admin.chat_id == admin_id)
        admin_name = admin.first_name

        admin.delete_instance()

        await query.message.edit_text(
            ADMIN_REMOVED_SUCCESSFULLY.format(admin_name)
        )

        # Notify the removed admin
        try:
            await client.send_message(
                chat_id=admin_id,
                text=ADMIN_REMOVED_NOTIFICATION
            )
        except Exception as e:
            logger.error(f"Failed to notify removed admin: {e}")

    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        await query.message.edit(ADMIN_REMOVAL_FAILED.format(str(e)))

@Client.on_callback_query(filters.regex(r"^cancel_admin_removal"), group=21)
async def cancel_admin_removal(client: Client, query: CallbackQuery):
    """Cancel admin removal process"""
    await query.message.edit_text(OPERATION_CANCELED)

async def send_message_to_all_users(client: Client, query: CallbackQuery):
    users = User.select()
    admin_chat_id = query.message.chat.id
    msg = await client.ask(chat_id=admin_chat_id, text=SEND_YOUR_MESSAGE, reply_markup=CANCEL_KEYBOARD)

    if msg.text == CANCEL:
        await client.send_message(chat_id=admin_chat_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
        return
    
    blocked_users = []
    deactivated_users = []
    invalid_users = []

    try:
        for user in users:
            user_id = user.chat_id
            username = user.username
            if user_id == str(admin_chat_id):
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
                    await client.send_message(chat_id=admin_chat_id, text=f'Error: {e}', reply_markup=ReplyKeyboardRemove())
        
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

            await client.send_document(chat_id=admin_chat_id, document=file_path, caption=REPORT_FILE_CAPTION, reply_markup=ReplyKeyboardRemove())
            os.remove(file_path)
        else:
            await client.send_message(chat_id=admin_chat_id, text=PUBLIC_MESSAGE_SENT, reply_markup=ReplyKeyboardRemove())
    
    except Exception as e:
        await client.send_message(chat_id=admin_chat_id, text=f'Error: {e}', reply_markup=ReplyKeyboardRemove())

async def show_bot_users(client: Client, query: CallbackQuery):
    users = User.select()
    admin_chat_id = query.message.chat.id

    await display_bot_users(client, admin_chat_id, users, page=1)

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

async def send_new_post_notification(client: Client, query: CallbackQuery):
    admin_chat_id = query.message.chat.id
    while True:
        msg = await client.ask(chat_id=admin_chat_id, text=SEND_POST_MESSAGE, reply_markup=CANCEL_KEYBOARD)

        if msg.text == CANCEL:
            await client.send_message(chat_id=admin_chat_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            return
        
        if not msg.text:
            await client.send_message(chat_id=admin_chat_id, text=SEND_ONLY_TEXT)
            continue
        
        while True:
            reply_markup_url = await client.ask(
                chat_id=admin_chat_id,
                text=SEND_POST_LINK_TEXT
            )
            if reply_markup_url.text == CANCEL:
                await client.send_message(chat_id=admin_chat_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return

            if not re.match(r'^(http|https)://', reply_markup_url.text):
                await client.send_message(chat_id=admin_chat_id, text=INVALID_POST_LINK, reply_markup=ReplyKeyboardRemove())
                continue

            view_post_button_text = await client.ask(
                chat_id=admin_chat_id,
                text=SEND_BUTTON_TEXT
            )
            if view_post_button_text.text == CANCEL:
                await client.send_message(chat_id=admin_chat_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return

            if not view_post_button_text.text:
                await client.send_message(chat_id=admin_chat_id, text=SEND_ONLY_TEXT)
                continue

            notification_keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text=view_post_button_text.text, url=reply_markup_url.text)]
                ]
                )

            post_sends_where = await client.ask(
                chat_id=admin_chat_id,
                text=NOTIF_SENT_PLACE_TEXT,
                reply_markup=ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD
            )

            if post_sends_where.text == CANCEL:
                await client.send_message(chat_id=admin_chat_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
                return
            
            if post_sends_where.text == TO_USERS_TEXT:
                users = User.select()
                if users:
                    for user in users:
                        user_id = user.chat_id
                        if user_id == str(admin_chat_id):
                            continue
                        await client.send_message(chat_id=user_id, text=msg.text, reply_markup=notification_keyboard)
                    await client.send_message(chat_id=admin_chat_id, text=PUBLIC_MESSAGE_SENT, reply_markup=ReplyKeyboardRemove())
                    break
                else:
                    await client.send_message(chat_id=admin_chat_id, text=NO_USERS_TEXT, reply_markup=ReplyKeyboardRemove())
                    break
            elif post_sends_where.text == TO_CHANNEL_TEXT:
                await client.send_message(chat_id=TAKBAND_QANDEEL, text=msg.text, reply_markup=notification_keyboard)
                await client.send_message(chat_id=admin_chat_id, text=MESSAGE_SENT_TO_CHANNEL_TEXT, reply_markup=ReplyKeyboardRemove())
                break
            else:
                await client.send_message(chat_id=admin_chat_id, text=INVALID_SELECTION_TEXT, reply_markup=ReplyKeyboardRemove())
                continue
        break

async def show_users_searches(client: Client, query: CallbackQuery):
    admin_chat_id = query.message.chat.id
    while True:
        user_id_input = await client.ask(chat_id=admin_chat_id, text=SEND_USER_ID, reply_markup=CANCEL_KEYBOARD)
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(chat_id=admin_chat_id, text=OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
            break

        # Check if input is numeric or a username
        if user_id.isdigit():
            # Treat input as chat_id
            user = User.get_or_none(User.chat_id == int(user_id))
        else:
            # Treat input as username (case-insensitive)
            user = User.get_or_none(fn.Lower(User.username) == user_id.lower())

        if not user:
            await client.send_message(chat_id=admin_chat_id, text=WRONG_USER_ID, reply_markup=ReplyKeyboardRemove())
            continue  # Restart the loop to prompt for an existing user ID
        
        user_searches = SearchHistory.select().where(SearchHistory.user == user).order_by(SearchHistory.search_date.desc())

        if not user_searches.exists():
            await client.send_message(chat_id=admin_chat_id, text=NO_SEARCHES_HISTORY_TEXT, reply_markup=ReplyKeyboardRemove())
            continue

        # Display the first page of results
        await display_searches_page(client, query,admin_chat_id, user, user_searches, page=1)
        break

async def display_searches_page(client: Client, query: CallbackQuery, chat_id, user, searches, page, edit=False):
    total_searches = searches.count()
    total_pages = (total_searches + SEARCHES_PER_PAGE - 1) // SEARCHES_PER_PAGE
    start_index = (page - 1) * SEARCHES_PER_PAGE
    end_index = start_index + SEARCHES_PER_PAGE
    admin_chat_id = query.message.chat.id

    # Get searches for the current page
    searches_on_page = searches[start_index:end_index]

    formatted_searches = "\n".join(
        [f"{search.search_date}: {search.search_term}" for search in searches_on_page]
    )

    text = f"Search history for {user.first_name} (Page {page}/{total_pages}):\n\n{formatted_searches}"

    # Pagination buttons
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(PREVIOUS_PAGE, callback_data=f"searches_prev_{page - 1}_{user.chat_id}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(NEXT_PAGE, callback_data=f"searches_next_{page + 1}_{user.chat_id}"))

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
        buttons.append(InlineKeyboardButton(PREVIOUS_PAGE, callback_data=f"users_prev_{page - 1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(NEXT_PAGE, callback_data=f"users_next_{page + 1}"))

    keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
    
    if not edit:
        global users_message
        users_message = await client.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
    if edit:
        await client.edit_message_text(chat_id=admin_id, message_id=users_message.id, text=text, reply_markup=keyboard)

async def delete_users_searches(client: Client, query: CallbackQuery):
    admin_chat_id = query.message.chat.id
    while True:
        user_id_input = await client.ask(
            chat_id=admin_chat_id,
            text=SEND_USER_ID,
            reply_markup=CANCEL_KEYBOARD
        )
        user_id = user_id_input.text.strip()

        if user_id == CANCEL:
            await client.send_message(
                chat_id=admin_chat_id,
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
                chat_id=admin_chat_id,
                text=WRONG_USER_ID,
                reply_markup=ReplyKeyboardRemove()
            )
            continue  # Restart the loop to prompt for an existing user ID

        # Delete user's search history
        try:
            deleted_count = SearchHistory.delete().where(SearchHistory.user == user).execute()
            await client.send_message(
                chat_id=admin_chat_id,
                text=f"Deleted {deleted_count} search(es) for user {user.first_name} ({user.chat_id})."
            )
            break
        except Exception as e:
            await client.send_message(chat_id=admin_chat_id, text=f"An error occurred: {e}")
            break

@Client.on_callback_query(admin_filter, group=1)
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
            await query.answer(USER_NOT_FOUND, show_alert=True)
            return

        searches = SearchHistory.select().where(SearchHistory.user == user).order_by(SearchHistory.search_date.desc())
        if not searches.exists():
            await query.answer(NO_SEARCHES_FOUND, show_alert=True)
            return

        # Update the message with the new page
        await display_searches_page(client, query, admin_id, user, searches, page, edit=True)
        await query.answer()  # Acknowledge the callback query

@Client.on_callback_query(admin_filter, group=3)
async def handle_users_pagination_buttons(client: Client, query: CallbackQuery):
    data = query.data
    users = User.select()
    admin_chat_id = query.message.chat.id

    if data.startswith("users_"):
        # Parse the callback data
        _, action, page = data.split("_")
        page = int(page)

        # Update the message with the new page
        await display_bot_users(client, admin_chat_id, users, page, edit=True)
        await query.answer()  # Acknowledge the callback query

async def channel_settings_command(client: Client, message: Message):
    """Show channel settings menu"""
    settings = load_channel_settings()
    required_channels = settings.get("required_channels", [])
    
    text = f"{CHANNEL_SETTINGS}\n\n"
    text += F"{REQUIRED_CHANNEL_FOR_USERS}\n\n"
    
    if not required_channels:
        text += f"{NO_CHANNEL_REQUIRED}"
    else:
        for i, channel in enumerate(required_channels, 1):
            text += f"{i}. {channel.get('name')} (`{channel.get('id')}`)\n"
    
    keyboard = [
        [InlineKeyboardButton(f"{ADD_CHANNEL}", callback_data="add_channel")],
        [InlineKeyboardButton(f"{REMOVE_CHANNEL}", callback_data="remove_channel")]
    ]
    
    await message.reply(text, reply_markup=InlineKeyboardMarkup(keyboard))

@Client.on_callback_query(filters.regex(r"^add_channel$"))
async def add_channel_callback(client, callback_query):
    """Prompt for adding a channel"""
    await callback_query.edit_message_text(PLEASE_SEND_CHANNEL_INFO)
    
    # Set user state
    admin_states[callback_query.from_user.id] = "waiting_for_channel_info"

@Client.on_callback_query(filters.regex(r"^remove_channel$"))
async def remove_channel_callback(client, callback_query):
    """Show channels to remove"""
    settings = load_channel_settings()
    required_channels = settings.get("required_channels", [])
    
    if not required_channels:
        await callback_query.edit_message_text(NO_CHANNEL_TO_REMOVE)
        return
    
    keyboard = []
    for i, channel in enumerate(required_channels):
        keyboard.append([
            InlineKeyboardButton(
                f"{channel.get('name')} ({channel.get('id')})", 
                callback_data=f"remove_channel_{i}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(BACK_CHANNEL_SETTINGS, callback_data="back_to_channel_settings")])
    
    await callback_query.edit_message_text(
        SELECT_CHANNEL_TO_REMOVE,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex(r"^remove_channel_(\d+)$"))
async def remove_specific_channel(client, callback_query):
    """Remove a specific channel"""
    # Extract the index from the callback data
    match = re.match(r"^remove_channel_(\d+)$", callback_query.data)
    if match:
        index = int(match.group(1))
        
        settings = load_channel_settings()
        required_channels = settings.get("required_channels", [])
        
        if 0 <= index < len(required_channels):
            removed_channel = required_channels.pop(index)
            settings["required_channels"] = required_channels
            save_channel_settings(settings)
            
            await callback_query.answer(CHANNEL_X_REMOVED.format(removed_channel.get('name')))
            
            # Update the message with current settings
            await channel_settings_command(client, callback_query.message)
        else:
            await callback_query.answer("Invalid channel index!")
    else:
        await callback_query.answer("Invalid callback data!")

@Client.on_callback_query(filters.regex(r"^back_to_channel_settings$"))
async def back_to_channel_settings(client, callback_query):
    """Go back to channel settings menu"""
    await channel_settings_command(client, callback_query.message)

@Client.on_message(admin_filter & filters.text, group=-1)
async def handle_admin_channel_input(client, message):
    """Handle admin input for channel settings"""
    user_id = message.from_user.id
    
    if user_id in admin_states and admin_states[user_id] == "waiting_for_channel_info":
        # Parse channel info
        parts = message.text.strip().split('|')
        
        if len(parts) == 3:
            channel_id, channel_name, channel_link = parts
            
            try:
                # Try to convert channel_id to int if it's numeric
                if channel_id.startswith('-100') and channel_id[4:].isdigit():
                    channel_id = int(channel_id)
                
                # Load current settings
                settings = load_channel_settings()
                required_channels = settings.get("required_channels", [])
                
                # Check if channel already exists
                for channel in required_channels:
                    if str(channel.get("id")) == str(channel_id):
                        await message.reply(CHANNEL_X_ALREADY_EXISTS.format(channel_name))
                        del admin_states[user_id]
                        # Stop message propagation
                        message.stop_propagation()
                        return True
                
                # Add new channel
                required_channels.append({
                    "id": channel_id,
                    "name": channel_name,
                    "link": channel_link
                })
                
                settings["required_channels"] = required_channels
                save_channel_settings(settings)
                
                await message.reply(CHANNEL_X_ADDED_TO_REQUIRED.format(channel_name))
                
                # Clear user state
                del admin_states[user_id]
                # Stop message propagation
                message.stop_propagation()
                return True
            except Exception as e:
                logger.error(f"Error adding channel: {e}")
                await message.reply("Error adding channel. Please check the format and try again.")
                # Stop message propagation
                message.stop_propagation()
                return True
        else:
            await message.reply("Invalid format. Please use: `channel_id|channel_name|channel_link`")
            # Stop message propagation
            message.stop_propagation()
            return True
    
    return False

