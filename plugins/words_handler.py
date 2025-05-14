from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from models.words import SayadGanj
from peewee import DoesNotExist
from constants.bot_messages import PLEASE_CHOOSE_ONE, WORD_NOT_FOUND, INLINE_RESULT_NOT_FOUND_TITLE, INLINE_RESULT_NOT_FOUND_DESC, INLINE_RESULT_INPUT_MSG_CONTENT
from main import config
from models.users import save_search
from filters.join_checker_filter import is_joined_filter
import re
import logging
from utils.state_manager import is_user_in_state, get_user_state
from plugins.admin import is_admin

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

admin_id = int(config.admin_id)

# Import user_states from word_of_day.py to check if admin is setting time
try:
    from plugins.word_of_day import user_states
except ImportError:
    # If import fails, create an empty dictionary
    user_states = {}

@Client.on_message(filters.text & filters.private & ~filters.via_bot & ~filters.regex(r"^\/") & is_joined_filter, group=10)
async def search_word_handler(client: Client, message: Message):
    # Skip processing if the user is in any special state
    user_id = message.from_user.id
    
    # Check if user is in any state that should prevent search
    if is_user_in_state(user_id):
        state = get_user_state(user_id)
        # Skip if user is waiting for feedback or admin is replying
        if state == "waiting_for_feedback" or state.startswith("replying_to_") or state == "waiting_for_wod_time":
            logger.info(f"Skipping search due to user state: {state}")
            return
    
    # Check if user is admin and in a state for setting word of day time
    if is_admin(user_id) and user_id in user_states and user_states[user_id] == "waiting_for_wod_time":
        # Check if the message looks like a time format (HH:MM)
        if re.match(r"^\d{1,2}:\d{1,2}$", message.text.strip()):
            logger.info(f"Forwarding time input to word_of_day handler: {message.text}")
            # Import the handler function directly
            from plugins.word_of_day import handle_admin_input
            # Forward the message to the word_of_day handler
            await handle_admin_input(client, message)
            return
    
    # Continue with search handling
    balochi_word = message.text
    
    # Log the search attempt for debugging
    logger.info(f"Searching for word: {balochi_word} from user: {message.chat.id}")
    
    # Save the search term to the database
    save_search(chat_id=message.chat.id, search_term=balochi_word)

    # Get search results
    results = await search_word(balochi_word)
    
    # Log the search results for debugging
    logger.info(f"Search results for '{balochi_word}': {len(results) if results else 0} results found")

    if results and len(results) > 0:  # Make sure results is not None and not empty
        if len(results) == 1:
            cleaned_translation = results[0].definition
            if len(cleaned_translation) > 4096:
                chunks = chunck_text(cleaned_translation)
                # Send first chunk
                await message.reply_text(chunks[0])
                # Send remaining chunks
                for chunk in chunks[1:]:
                    await message.reply_text(chunk)
            else:
                await message.reply_text(cleaned_translation)
        else:
            buttons = []
            for result in results:
                cleaned_translation = result.definition      
                splited_text = cleaned_translation.split(':')

                if splited_text[0].startswith('\n'):
                    text_to_display = splited_text[0].split('\n')[1].strip()
                elif splited_text[0].startswith('<h'):
                    text_to_display = splited_text[0]
                else:
                    text_to_display = splited_text[0]

                buttons.append(
                    [InlineKeyboardButton(text=text_to_display, callback_data=f"result_{result.id}")]
                )
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=message.chat.id,
                text=PLEASE_CHOOSE_ONE,
                reply_markup=reply_markup
            )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text=WORD_NOT_FOUND.format(balochi_word)
        )

active_buttons = {}

# Change this:
@Client.on_callback_query(filters.regex(r'^result_'), group=2)
# To:
@Client.on_callback_query(filters.regex(r'^result_'), group=20)

# Change this:
@Client.on_inline_query()
# To:
@Client.on_inline_query(group=20)
async def callback_handler(client: Client, query: CallbackQuery):
    message = query.message
    chat_id = message.chat.id
    
    if query.data.startswith("result_"):
        result_id = int(query.data.split("_")[1])
        try:
            selected_result = SayadGanj.select().where(
                SayadGanj.id == result_id,).get()
            full_text = selected_result.definition

            if len(full_text) > 4096:
                chunks = chunck_text(full_text)

                # Edit the message with the first chunk
                await query.edit_message_text(chunks[0])

                # Send the remaining chunks as new messages
                for chunk in chunks[1:]:
                    await client.send_message(chat_id=chat_id, text=chunk)
            else:
                await query.edit_message_text(full_text)

            # Remove the selected button
            if chat_id in active_buttons and result_id in active_buttons[chat_id]:
                active_buttons[chat_id].remove(result_id)
            
            keyboard = query.message.reply_markup.inline_keyboard
            new_buttons = []
            for row in keyboard:
                new_row = []
                for button in row:
                    if int(button.callback_data.split("_")[1]) == result_id:
                        # Add the "▫️" to the selected button
                        if not button.text.startswith("▫️ "):
                            new_text = "▫️ " + button.text
                        else:
                            new_text = button.text
                    else:
                        # Remove the "▫️" from other buttons
                        new_text = button.text.replace("▫️ ", "")
                    new_row.append(InlineKeyboardButton(text=new_text, callback_data=button.callback_data))
                new_buttons.append(new_row)
                
            await query.edit_message_reply_markup(InlineKeyboardMarkup(new_buttons))

        except DoesNotExist:
            await query.answer('No results found.')
        except Exception:
            await query.answer('An error occurred.')


MAX_RESULTS = 50  # Maximum number of results to return
MAX_TITLE_LENGTH = 50  # Maximum length for the title
MAX_DESC_LENGTH = 200  # Maximum length for the description

# Inline query handler
@Client.on_inline_query()
async def inline_query_handler(client: Client, inline_query: InlineQuery):
    query = inline_query.query

    results = await inline_search_word(query)
    inline_results = []
    if results:
        total_length = 0
        for result in results:
            cleaned_translation = result.definition
            splited_text = cleaned_translation.split(':', 1)
            cleaned_title = splited_text[0].strip()[:MAX_TITLE_LENGTH]
            cleaned_desc = f'{cleaned_title}:\n{splited_text[1].strip()}'

            # Check if cleaned_title or cleaned_desc are empty
            if not cleaned_title or not cleaned_desc:
                logger.warning(f"Empty title or description for result: {result}")
                continue

            input_content = InputTextMessageContent(cleaned_desc)
            inline_result = InlineQueryResultArticle(
                id=str(result.id),
                title=cleaned_title,
                description=cleaned_desc,
                input_message_content=input_content
            )

            # Estimate the length of the current result
            result_length = len(cleaned_title) + len(cleaned_desc) + 50  # Rough estimate including overhead
            total_length += result_length

            # If total_length exceeds a certain threshold, stop adding more results
            if total_length > 4000:  # Telegram's total length limit for inline query results
                break

            inline_results.append(inline_result)
    else:
        # Create a result indicating no results were found
        inline_result = InlineQueryResultArticle(
            id="no_results",
            title=INLINE_RESULT_NOT_FOUND_TITLE,
            description=INLINE_RESULT_NOT_FOUND_DESC.format(query),
            input_message_content=InputTextMessageContent(INLINE_RESULT_INPUT_MSG_CONTENT)
        )
        inline_results.append(inline_result)

    await inline_query.answer(inline_results)

    
async def search_word(word_to_trans):
    try:
        # First try exact match
        exact_results = SayadGanj.select().where(
            (SayadGanj.full_word == word_to_trans) | 
            (SayadGanj.full_word_with_symbols == word_to_trans)
        ).execute()
        
        exact_results_list = list(exact_results)
        
        # If exact match found, return it
        if exact_results_list and len(exact_results_list) > 0:
            logger.info(f"Found {len(exact_results_list)} exact results for '{word_to_trans}'")
            return exact_results_list
        
        # If no exact match, try partial match
        partial_results = SayadGanj.select().where(
            (SayadGanj.full_word.contains(word_to_trans))
        ).limit(10).execute()
                #    (SayadGanj.full_word_with_symbols.contains(word_to_trans)) 
        partial_results_list = list(partial_results)
        logger.info(f"Found {len(partial_results_list)} partial results for '{word_to_trans}'")
        return partial_results_list
        
    except DoesNotExist:
        logger.info(f"No results found for '{word_to_trans}'")
        return []
    except Exception as e:
        logger.error(f"Error searching for '{word_to_trans}': {str(e)}")
        return []

async def inline_search_word(word_to_trans):
    try:
        query_pattern = f"%{word_to_trans}%"
        results = (SayadGanj
                   .select()
                   .where((SayadGanj.full_word == word_to_trans) | 
                          (SayadGanj.full_word.contains(word_to_trans)))
                   .limit(MAX_RESULTS)
                   .execute())
        return results
    except DoesNotExist:
        return None

def chunck_text(full_text):
    chunks = [full_text[i:i + 4096] for i in range(0, len(full_text), 4096)]
    return chunks