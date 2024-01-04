from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from constants.join_checker_filter import is_joined_filter
from models.words import WordBook
from peewee import DoesNotExist
import logging
import re

@Client.on_message(filters.text & is_joined_filter)
async def search_word_handler(client: Client, message: Message):
    balochi_word = message.text
    results = await search_word(balochi_word)
    if results:
        if len(results) < 1:
            await message.reply_text("No results found.")
        elif len(results) == 1:
            # Display the only result
            cleaned_translation = remove_h_tags(results[0].entry)
            await message.reply_text(cleaned_translation)
        else:
            buttons = []
            for result in results:
                cleaned_translation = remove_h_tags(result.entry.replace('\n', ''))
                splited_text = cleaned_translation.split(':')
                if len(splited_text) > 1:
                    text_to_display = splited_text[0]
                else:
                    text_to_display = splited_text

                buttons.append(
                    [InlineKeyboardButton(text=text_to_display, callback_data=f"result_{result._id}")]
                )
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=message.chat.id,
                text="Please choose one:",
                reply_markup=reply_markup
            )

active_buttons = {}

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    chat_id = query.message.chat.id
    if query.data.startswith("result_"):
        result_id = int(query.data.split("_")[1])
        try:
            # Fetch the specific result based on the ID (you'll need to implement this logic)
            selected_result = WordBook.select().where(
                WordBook._id == result_id,
            ).get()

            await query.edit_message_text(selected_result.entry)
            # Remove the selected button
            if chat_id in active_buttons and result_id in active_buttons[chat_id]:
                active_buttons[chat_id].remove(result_id)
            
            keyboard = query.message.reply_markup.inline_keyboard
            new_buttons = []
            for row in keyboard:
                new_row = []
                for button in row:
                    if int(button.callback_data.split("_")[1]) not in active_buttons.get(chat_id, []):
                        new_row.append(button)
                        new_buttons.append(new_row)
            
            # Edit the message with the updated inline keyboard
            await query.edit_message_reply_markup(InlineKeyboardMarkup(new_buttons))
        except DoesNotExist:
            await query.answer('No results found.')
        except Exception as e:
            await query.answer('An error occurred.')


# Inline query handler
@Client.on_inline_query()
async def inline_query_handler(client: Client, inline_query: InlineQuery):
    results = await search_word(inline_query.query)  # Perform your search based on the query
    
    inline_results = []
    for result in results:
        # Create InlineQueryResultArticle for each result
        cleaned_entry = remove_h_tags(result.entry.split(':')[1])  # Adjust as needed
        input_content = InputTextMessageContent(cleaned_entry)
        inline_result = InlineQueryResultArticle(
            id=str(result._id),
            title=cleaned_entry,
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
    except DoesNotExist as e:
        pass
    
def remove_h_tags(word):
    new_word = re.sub(r'<h1>.*?</h1>', '', word)
    return new_word
