from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from constants.bot_messages import SUB_CHANNEL_NAME, SUB_CHANNEL_LINK, INLINE_SEARCH_TITLE, SAYADGANJ_WEBSITE_LINK, SAYADGANJ_WEBSITE_TITLE
from constants.bot_messages import (
    BOT_USERS,
    SEND_PUBLIC_MESSAGE,
    SEND_PRIVATE_MESSAGE,
    BOT_USERS_CD,
    PUBLIC_MESSAGE,
    PRIVATE_MESSAGE,
    EXIT,
    EXIT_BUTTON_DATA,
    CANCEL,
    NEW_POST_CALLBACK_TEXT,
    NEW_POST_KEYBOARD_TEXT,
    TO_USERS_TEXT,
    TO_CHANNEL_TEXT,
    )

JOIN_TO_CHANNEL_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(SUB_CHANNEL_NAME, url=SUB_CHANNEL_LINK)]
    ]
    )

# Inline keyboard button
INLINE_SEARCH_BUTTON = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(INLINE_SEARCH_TITLE, switch_inline_query="")]
    ]
    )

SAYADGANJ_WEBAPP_BUTTON = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(SAYADGANJ_WEBSITE_TITLE, web_app=WebAppInfo(url=SAYADGANJ_WEBSITE_LINK))]
    ]
)

CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton(CANCEL)]
    ],
    resize_keyboard=True
)

ADMIN_OPTIONS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(BOT_USERS, callback_data=BOT_USERS_CD)],
        [
            InlineKeyboardButton(SEND_PUBLIC_MESSAGE, callback_data=PUBLIC_MESSAGE),
            InlineKeyboardButton(SEND_PRIVATE_MESSAGE, callback_data=PRIVATE_MESSAGE)
        ],
        [
            InlineKeyboardButton(NEW_POST_KEYBOARD_TEXT, callback_data=NEW_POST_CALLBACK_TEXT)
        ],
        [InlineKeyboardButton(EXIT, callback_data=EXIT_BUTTON_DATA)]
    ]
)

ADMIN_CHOOSE_WHERE_POST_SENDS_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton(text=TO_USERS_TEXT), KeyboardButton(text=TO_CHANNEL_TEXT)],
        [KeyboardButton(text=CANCEL)]
    ],
    resize_keyboard=True
)