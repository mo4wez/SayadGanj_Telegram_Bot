# from pyrogram import Client, filters
# from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
# from constants.keyboards import JOIN_TO_CHANNEL_KEYBOARD_1, JOIN_TO_CHANNEL_KEYBOARD_2
# from constants.bot_messages import (
#     TAKBAND_QANDEEL,
#     MEME_CHANNEl,
#     JOINED,
#     NOT_JOINED,
#     MEMEBER_STATUS_UNKNOWN,
#     MEMBER_STATUS_LIST,
#     FORCE_JOIN_MESSAGE
#     )

# async def is_user_joined(_, client: Client, message: Message):
#     chat_id = message.chat.id

#     status_channel_1 = MEMEBER_STATUS_UNKNOWN
#     status_channel_2 = MEMEBER_STATUS_UNKNOWN

#     try:
#         user_in_channel_1 = await client.get_chat_member(
#             chat_id=TAKBAND_QANDEEL,
#             user_id=chat_id,
#         )
#         status_channel_1 = JOINED if user_in_channel_1.status not in MEMBER_STATUS_LIST else NOT_JOINED
#     except Exception as e:
#         status_channel_1 = NOT_JOINED

#     try:
#         user_in_channel_2 = await client.get_chat_member(
#             chat_id=MEME_CHANNEl,
#             user_id=chat_id,
#         )
#         status_channel_2 = JOINED if user_in_channel_2.status not in MEMBER_STATUS_LIST else NOT_JOINED
#     except Exception as e:
#         status_channel_2 = NOT_JOINED


#     message_text = FORCE_JOIN_MESSAGE.format(
#         status_channel_1,
#         status_channel_2
#     )
#     reply_markup = None
    
#     if status_channel_1 == NOT_JOINED and status_channel_2 == NOT_JOINED:
#         reply_markup = InlineKeyboardMarkup(
#             [[JOIN_TO_CHANNEL_KEYBOARD_1], [JOIN_TO_CHANNEL_KEYBOARD_2]]
#         )
#     elif status_channel_1 == NOT_JOINED:
#         reply_markup = InlineKeyboardMarkup([[JOIN_TO_CHANNEL_KEYBOARD_1]])
#     elif status_channel_2 == NOT_JOINED:
#         reply_markup = InlineKeyboardMarkup([[JOIN_TO_CHANNEL_KEYBOARD_2]])

#     if status_channel_1 == JOINED and status_channel_2 == JOINED:
#         return True
#     else:
#         await client.send_message(
#             chat_id=chat_id,
#             text=message_text,
#             reply_markup=reply_markup
#         )
#         return False

# is_joined_filter = filters.create(is_user_joined)


from pyrogram import Client, filters
from pyrogram.types import Message
from constants.keyboards import JOIN_TO_CHANNEL_KEYBOARD_1
from constants.bot_messages import PLEASE_JOIN_TO_CHANNEL, BALOCHBIT

async def is_user_joined(_, client: Client, message: Message):
    chat_id = message.chat.id
    try:
        user = await client.get_chat_member(
            chat_id=BALOCHBIT,
            user_id=chat_id,
        )
        if user.status == "left" or user.status == "kicked":
            return False
        else:
            return True
    except Exception as e:
        await client.send_message(
            chat_id=chat_id,
            text=PLEASE_JOIN_TO_CHANNEL,
            reply_markup=JOIN_TO_CHANNEL_KEYBOARD_1
        )
        return False
    
is_joined_filter = filters.create(is_user_joined)