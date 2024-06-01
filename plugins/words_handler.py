import re
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from filters.join_checker_filter import is_user_joined
from models.words import WordBook
from peewee import DoesNotExist
from constants.bot_messages import PLEASE_CHOOSE_ONE, WORD_NOT_FOUND
from main import config

admin_id = int(config.admin_id)

@Client.on_message((filters.text))
async def search_word_handler(client: Client, message: Message):
    if not await is_user_joined(None, client, message):
        return

    balochi_word = message.text
    results = await search_word(balochi_word)
    if results:
        if len(results) < 1:
            await message.reply_text("No results found.")
        elif len(results) == 1:
            cleaned_translation = remove_first_line(results[0].entry)
            await message.reply_text(cleaned_translation)
        else:
            buttons = []
            for result in results:
                cleaned_translation = remove_first_line(result.entry)
                splited_text = cleaned_translation.split(':')
                text_to_display = splited_text[0]

                buttons.append(
                    [InlineKeyboardButton(text=text_to_display, callback_data=f"result_{result._id}")]
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
            text=WORD_NOT_FOUND
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
            selected_result = WordBook.select().where(
                WordBook._id == result_id,).get()
            full_text = remove_first_line(selected_result.entry)

            if len(full_text) > 4096:
                # Split the full_text into chunks of 4096 characters
                chunks = [full_text[i:i + 4096] for i in range(0, len(full_text), 4096)]

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


# Inline query handler
@Client.on_inline_query()
async def inline_query_handler(client: Client, inline_query: InlineQuery):

    results = await search_word(inline_query.query)

    inline_results = []
    for result in results:
        cleaned_translation = remove_first_line(result.entry)
        splited_text = cleaned_translation.split(':')
        cleaned_title = splited_text[0]
        cleaned_desc = splited_text[1]

        input_content = InputTextMessageContent(cleaned_desc)
        inline_result = InlineQueryResultArticle(
            id=str(result._id),
            title=cleaned_title,
            description=cleaned_desc,
            input_message_content=input_content
        )
        inline_results.append(inline_result)

    await inline_query.answer(inline_results)
    
async def search_word(word_to_trans):
    try:
        results = WordBook.select().where(
            WordBook.langFullWord == word_to_trans
        )
        return results
    except DoesNotExist:
        return None

def remove_first_line(text):
    # Split the text into lines
    lines = text.split('\n')
    # Remove the first line
    remaining_lines = lines[1:]
    # Join the remaining lines back into a single string
    new_text = '\n'.join(remaining_lines)
    return new_text
