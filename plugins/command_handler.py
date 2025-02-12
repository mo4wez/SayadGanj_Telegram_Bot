import logging
import jdatetime
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from filters.join_checker_filter import is_user_joined
from models.users import User
from constants.bot_messages import WELCOME_MESSAGE, INLINE_SEARCH_BODY, TUTORIAL_VIDEO_FORWARD_FAILED, TAKBAND_QANDEEL
from constants.keyboards import INLINE_SEARCH_BUTTON, SAYADGANJ_WEBAPP_BUTTON
from main import config
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

admin_id = int(config.admin_id)

@Client.on_message(filters.command('start'))
async def start(client: Client, message: Message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    if not await is_user_joined(None, client, message):
        return

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

@Client.on_message(filters.command('search'))
async def search(client: Client, message: Message):
    chat_id = message.chat.id
    
    if not await is_user_joined(None, client, message):
        return
    
    await client.send_message(
        chat_id=chat_id,
        text=INLINE_SEARCH_BODY,
        reply_markup=INLINE_SEARCH_BUTTON
    )

@Client.on_message(filters.command('tutorial'))
async def tutorial(client: Client, message: Message):
    channel_id = "sayadganjarc"
    message_id = 4

    if not await is_user_joined(None, client, message):
        return

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