from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from constants.bot_messages import SUB_CHANNEL_NAME, SUB_CHANNEL_LINK, INLINE_SEARCH_TITLE

JOIN_TO_CHANNEL_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(SUB_CHANNEL_NAME, url=SUB_CHANNEL_LINK)]
    ]
    )

# Inline keyboard button
INLINE_SEARCH_BUTTON = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(INLINE_SEARCH_TITLE, switch_inline_query_current_chat="")]
    ]
    )
