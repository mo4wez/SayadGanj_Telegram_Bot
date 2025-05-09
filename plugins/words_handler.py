from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from filters.join_checker_filter import is_user_joined
from models.words import SayadGanj
from peewee import DoesNotExist
from constants.bot_messages import PLEASE_CHOOSE_ONE, WORD_NOT_FOUND, INLINE_RESULT_NOT_FOUND_TITLE, INLINE_RESULT_NOT_FOUND_DESC, INLINE_RESULT_INPUT_MSG_CONTENT
from main import config
from models.users import save_search

import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

admin_id = int(config.admin_id)

@Client.on_message((~filters.via_bot & ~filters.regex(r"^\/") & filters.text & filters.private))
async def search_word_handler(client: Client, message: Message):
    if not await is_user_joined(None, client, message):
        return

    balochi_word = message.text

    # Save the search term to the database
    save_search(chat_id=message.chat.id, search_term=balochi_word)

    results = await search_word(balochi_word)

    if results:
        if len(results) < 1:
            await message.reply_text("No results found.")
        elif len(results) == 1:
            cleaned_translation = results[0].definition
            if len(cleaned_translation) > 4096:
                chunks = chunck_text(cleaned_translation)
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

@Client.on_callback_query(filters.regex(r'^result_'), group=2)
async def callback_handler(client: Client, query: CallbackQuery):
    message = query.message
    chat_id = message.chat.id

    if not await is_user_joined(None, client, message):
        return
    
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
        results = SayadGanj.select().where(
            (SayadGanj.full_word == word_to_trans) | (SayadGanj.full_word_with_symbols == word_to_trans)
        ).execute()
        return results
    except DoesNotExist:
        return None

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