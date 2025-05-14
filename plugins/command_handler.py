import logging
import jdatetime
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from filters.join_checker_filter import is_joined_filter
from models.users import User
from constants.bot_messages import (
    WELCOME_MESSAGE,
    INLINE_SEARCH_BODY,
    TUTORIAL_VIDEO_FORWARD_FAILED,
    TAKBAND_QANDEEL,
    BOOK_INFO_NOT_AVAILABLE,
    NO_BOOKS_AVAILABLE,
    PLEASE_SELECT_A_BOOK_TO_DOWNLOAD,
    AN_ERROR_OCCURRED_FETCHING_BOOK_LIST,
    FAILED_TO_CLOSE_BOOK_MENU,
    SENDING_YOUR_BOOK,
    BOOK_SENT_ENJOY,
    FAILED_TO_SEND_THE_BOOK,
    CLOSE_BOOKS_LIST
)
from constants.keyboards import INLINE_SEARCH_BUTTON, SAYADGANJ_WEBAPP_BUTTON
from main import config
import os
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

admin_id = int(config.admin_id)

@Client.on_message(filters.command('start') & is_joined_filter)
async def start(client: Client, message: Message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    user = User.get_or_none(User.chat_id == chat_id)
    jalaali_date = jdatetime.datetime.now().strftime("%Y/%m/%d")

    if user:
        user.first_name = first_name
        user.username = username
        if not user.start_date:
            user.start_date = jalaali_date
        user.save()
    else:
        User.create(
            chat_id=chat_id,
            first_name=first_name,
            username=username,
            start_date=jalaali_date
        )
    await message.reply_text(WELCOME_MESSAGE, reply_markup=SAYADGANJ_WEBAPP_BUTTON)

@Client.on_message(filters.command('search') & is_joined_filter)
async def search(client: Client, message: Message):
    chat_id = message.chat.id
    
    await client.send_message(
        chat_id=chat_id,
        text=INLINE_SEARCH_BODY,
        reply_markup=INLINE_SEARCH_BUTTON
    )

@Client.on_message(filters.command('tutorial') & is_joined_filter)
async def tutorial(client: Client, message: Message):
    channel_id = "sayadganjarc"
    message_id = 4

    try:
        # Copy the video from the public channel to the user
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=channel_id,
            message_id=message_id
        )
    except Exception as e:
        logger.error(f"Failed to copy video: {e}")
        await message.reply(TUTORIAL_VIDEO_FORWARD_FAILED)

@Client.on_message(filters.command('promote') & filters.user(admin_id))
async def promote_me(client: Client, message: Message):
    try:
        await client.promote_chat_member(
            user_id=admin_id,
            chat_id=TAKBAND_QANDEEL,
            privileges=ChatPrivileges(
                can_change_info=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_restrict_members=True,
                can_pin_messages=False,
                can_promote_members=True,
                can_manage_video_chats=True,
            )
        )

        await message.reply('You promoted successfully.')

    except Exception as e:
        await message.reply(f'Error: {e}')

@Client.on_message(filters.command('get_books') & is_joined_filter)
async def get_books_command(client: Client, message: Message):
    """Display available books for the user to select"""
    try:
        # Load book information from JSON file
        books_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'book_info.json')
        
        if not os.path.exists(books_file_path):
            await message.reply(BOOK_INFO_NOT_AVAILABLE)
            logger.error(f"Book info file not found at {books_file_path}")
            return
            
        with open(books_file_path, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
        
        # Create keyboard with book buttons
        keyboard = []
        for book in book_data.get('books', []):
            book_id = book.get('id')
            book_name = book.get('name')
            book_author = book.get('author', 'Unknown')
            
            if book_id and book_name:
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{book_name} - {book_author}", 
                        callback_data=f"get_book_{book_id}"
                    )
                ])
        
        # Add a close button at the end
        keyboard.append([
            InlineKeyboardButton(
                text=CLOSE_BOOKS_LIST, 
                callback_data="close_books_menu"
            )
        ])
        
        if len(keyboard) <= 1:  # Only the close button
            await message.reply(NO_BOOKS_AVAILABLE)
            return
            
        # Send message with book selection buttons
        await message.reply(
            text=PLEASE_SELECT_A_BOOK_TO_DOWNLOAD,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in get_books_command: {e}")
        await message.reply(AN_ERROR_OCCURRED_FETCHING_BOOK_LIST)

@Client.on_callback_query(filters.regex(r"^close_books_menu$"))
async def close_books_menu(client: Client, callback_query: CallbackQuery):
    """Close the books menu and call the start command"""
    try:
        # Delete the message with the books menu
        await callback_query.message.delete()
        
        # Create a dummy message object to pass to the start command
        dummy_message = Message(
            id=0,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user,
            text="/start",
            client=client
        )
        
        # Call the start command
        await start(client, dummy_message)
        
    except Exception as e:
        logger.error(f"Error in close_books_menu: {e}")
        await callback_query.answer(FAILED_TO_CLOSE_BOOK_MENU)

@Client.on_callback_query(filters.regex(r"^get_book_(\d+)"))
async def send_selected_book(client: Client, callback_query: CallbackQuery):
    """Send the selected book to the user"""
    try:
        # Extract book ID from callback data
        book_id = int(callback_query.data.split('_')[2])
        channel_id = "sayadganjarc"
        user_chat_id = callback_query.message.chat.id
        
        # Acknowledge the request
        await callback_query.answer(SENDING_YOUR_BOOK)
        
        # Copy the book from the channel to the user
        await client.copy_message(
            chat_id=user_chat_id,
            from_chat_id=channel_id,
            message_id=book_id
        )
        
        # Edit the original message to show the book was sent
        await callback_query.edit_message_text(
            BOOK_SENT_ENJOY
        )
    except Exception as e:
        logger.error(f"Failed to send book: {e}")
        await callback_query.edit_message_text(
            FAILED_TO_SEND_THE_BOOK
        )