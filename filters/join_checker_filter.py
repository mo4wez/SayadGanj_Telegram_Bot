from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from constants.bot_messages import PLEASE_JOIN_TO_CHANNEL, TAKBAND_QANDEEL
import logging
import json
import os

# Configure logging
logger = logging.getLogger(__name__)

# Path to the channel settings file
CHANNEL_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "channel_settings.json")

# Default channel settings
DEFAULT_CHANNEL_SETTINGS = {
    "required_channels": [
        {
            "id": TAKBAND_QANDEEL,
            "name": "Takband Qandeel",
            "link": "https://t.me/takband_qandeel"
        }
    ]
}

def load_channel_settings():
    """Load channel settings from JSON file"""
    try:
        if os.path.exists(CHANNEL_SETTINGS_FILE):
            with open(CHANNEL_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default settings file if it doesn't exist
            save_channel_settings(DEFAULT_CHANNEL_SETTINGS)
            return DEFAULT_CHANNEL_SETTINGS
    except Exception as e:
        logger.error(f"Error loading channel settings: {e}")
        return DEFAULT_CHANNEL_SETTINGS

def save_channel_settings(settings):
    """Save channel settings to JSON file"""
    try:
        with open(CHANNEL_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving channel settings: {e}")

async def is_user_joined(_, client: Client, message: Message):
    """
    Check if a user has joined all required channels.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Load channel settings
    settings = load_channel_settings()
    required_channels = settings.get("required_channels", [])
    
    # If no channels are required, return True
    if not required_channels:
        return True
    
    # Check each required channel
    not_joined_channels = []
    
    for channel in required_channels:
        channel_id = channel.get("id")
        channel_name = channel.get("name")
        channel_link = channel.get("link")
        
        try:
            user = await client.get_chat_member(
                chat_id=channel_id,
                user_id=user_id,
            )
            
            # Log the user status for debugging
            logger.info(f"User {user_id} has status {user.status} in channel {channel_id}")
            
            # Check if user is a member, administrator, or creator
            status_str = str(user.status)
            
            if not ("administrator" in status_str.lower() or 
                   "member" in status_str.lower() or 
                   "owner" in status_str.lower() or 
                   "creator" in status_str.lower()):
                not_joined_channels.append({
                    "id": channel_id,
                    "name": channel_name,
                    "link": channel_link
                })
                
        except Exception as e:
            logger.error(f"Error checking channel membership for {channel_id}: {str(e)}")
            not_joined_channels.append({
                "id": channel_id,
                "name": channel_name,
                "link": channel_link
            })
    
    # If user has joined all channels, return True
    if not not_joined_channels:
        return True
    
    # Otherwise, send message with join buttons for channels not joined
    keyboard = []
    for channel in not_joined_channels:
        keyboard.append([InlineKeyboardButton(text=channel.get("name", "Join Channel"), url=channel.get("link"))])
    
    await client.send_message(
        chat_id=chat_id,
        text=PLEASE_JOIN_TO_CHANNEL,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return False

# Create the filter
is_joined_filter = filters.create(is_user_joined)