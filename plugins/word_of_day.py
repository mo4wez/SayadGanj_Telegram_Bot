import random
import asyncio
import schedule
import time
import threading
import logging
import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from models.words import SayadGanj
from constants.bot_messages import WORD_OF_DAY_TEXT, WORD_OF_DAY_WAS_SENT_TO_CHANNEL, ERROR_SENDING_WORD_OF_DAY_TO_CHANNEL, WORD_OF_DAY_SENT_X_OUT_OF_Y_USERS
from dotenv import load_dotenv
from models.users import User
from plugins.admin import admin_callback_handler, is_admin

# Load environment variables
load_dotenv()
admin_id = int(os.getenv('ADMIN_ID', 0))

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for scheduler
scheduler_thread = None
scheduler_thread_running = False
user_states = {}

# Default settings
DEFAULT_TIME = "12:30"
DEFAULT_TARGET = "channel"  # Can be "users" or "channel"
CHANNEL_ID = os.getenv('TAKBAND_QANDEEL', '')  # Get channel ID from env

# Settings file path
SETTINGS_FILE = "word_of_day_settings.json"

# Load settings
def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default settings
            settings = {
                "time": DEFAULT_TIME,
                "target": DEFAULT_TARGET
            }
            save_settings(settings)
            return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return {"time": DEFAULT_TIME, "target": DEFAULT_TARGET}

# Save settings
def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

# Global settings variable
settings = load_settings()

async def send_word_of_day(client):
    """Send a random word of the day to all users or channel"""
    # Get total count of words
    total_words = SayadGanj.select().count()
    
    # Get a random word
    random_id = random.randint(1, total_words)
    try:
        word = SayadGanj.get(SayadGanj.id == random_id)
        
        # Format the message
        message = WORD_OF_DAY_TEXT.format(
            word=word.full_word,
            definition=word.definition
        )
        
        # Load current settings
        current_settings = load_settings()
        target = current_settings.get("target", DEFAULT_TARGET)
        
        success_count = 0
        
        # Send based on target setting
        if target == "channel" and CHANNEL_ID:
            try:
                await client.send_message(
                    chat_id=int(CHANNEL_ID),
                    text=message
                )
                success_count = 1
                await client.send_message(
                    chat_id=admin_id,
                    text=f"{WORD_OF_DAY_WAS_SENT_TO_CHANNEL}"
                )
            except Exception as e:
                logger.error(f"Failed to send word of day to channel: {e}")
                await client.send_message(
                    chat_id=admin_id,
                    text=f"{ERROR_SENDING_WORD_OF_DAY_TO_CHANNEL}: {e}"
                )
        else:
            # Send to all uses except admins
            from models.admins import Admin
            # Send to all users
            users = User.select()

            admin_chat_ids = [admin.chat_id for admin in Admin.select()]

            if admin_id not in admin_chat_ids:
                admin_chat_ids.append(admin_id)

            total_users = 0
            
            for user in users:
                # Skip if user is an admin
                if int(user.chat_id) in admin_chat_ids:
                    continue
                total_users += 1
                try:
                    await client.send_message(
                        chat_id=int(user.chat_id),
                        text=message
                    )
                    success_count += 1
                    await asyncio.sleep(0.5)  # To avoid flood limits
                except Exception as e:
                    logger.error(f"Failed to send word of day to {user.chat_id}: {e}")
            
            # Notify admin
            await client.send_message(
                chat_id=admin_id,
                text=WORD_OF_DAY_SENT_X_OUT_OF_Y_USERS.format(success_count, total_users))
    except Exception as e:
        logger.error(f"Error sending word of day: {e}")
        await client.send_message(
            chat_id=admin_id,
            text=f"Error sending word of day: {e}"
        )

def run_scheduler(app):
    """Run the scheduler in a separate thread"""
    global scheduler_thread_running
    scheduler_thread_running = True
    
    # Clear existing jobs
    schedule.clear()
    
    # Load current settings
    current_settings = load_settings()
    scheduled_time = current_settings.get("time", DEFAULT_TIME)
    
    # Schedule the job
    schedule.every().day.at(scheduled_time).do(lambda: asyncio.run(send_word_of_day(app)))
    logger.info(f"Word of day scheduled for {scheduled_time}")
    
    while scheduler_thread_running:
        schedule.run_pending()
        time.sleep(60)
    
    logger.info("Scheduler thread stopping")
    
    # Remove this second infinite loop
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

# Command to manually send word of the day
@Client.on_message(filters.command("send_word_of_day") & filters.user(admin_id), group=0)
async def manual_send_word_of_day(client, message):
    await send_word_of_day(client)

# Command to set word of day settings
@Client.on_message(filters.command("send_word_of_day") & filters.create(lambda _, __, message: is_admin(message.from_user.id)), group=0)
async def word_of_day_settings(client, message):
    """Show word of day settings menu"""
    current_settings = load_settings()
    
    # Create settings keyboard
    keyboard = [
        [InlineKeyboardButton(f"⏰ وهد: {current_settings.get('time', DEFAULT_TIME)}", callback_data="wod_set_time")],
        [InlineKeyboardButton(f"📨 دیم دیگ په: {'چینل' if current_settings.get('target', DEFAULT_TARGET) == 'channel' else 'کارمرز کنوکاں'}", 
                             callback_data="wod_toggle_target")]
    ]
    
    await message.reply(
        "⚙️ روچ گال ءِ کاربوج\n\nچیر ءِ بٹناں یکے ءَ بجن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex(r"^wod_toggle_target$"))  # Remove the group parameter
async def toggle_target(client, callback_query):
    """Toggle between sending to users or channel"""
    current_settings = load_settings()
    
    # Toggle target
    current_target = current_settings.get("target", DEFAULT_TARGET)
    new_target = "channel" if current_target == "users" else "users"
    
    # Update settings
    current_settings["target"] = new_target
    save_settings(current_settings)
    
    # Update keyboard
    keyboard = [
        [InlineKeyboardButton(f"⏰ وهد: {current_settings.get('time', DEFAULT_TIME)}", callback_data="wod_set_time")],
        [InlineKeyboardButton(f"📨 دیم دیگ په: {'چینل' if new_target == 'channel' else 'کارمرز کنوکاں'}", 
                             callback_data="wod_toggle_target")]
    ]
    
    await callback_query.edit_message_text(
        f"⚙️ گال روچ ءِ کاربوج\n\n کار بوج بدل بوت، گال په {'چینل' if new_target == 'channel' else 'کارمرز کنوکاں'} دیم دیگ بیت.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Restart scheduler with new settings
    restart_scheduler(client)  # Fixed: removed .bot

@Client.on_callback_query(filters.regex(r"^wod_set_time$"))  # Remove the group parameter
async def set_time_prompt(client, callback_query):
    """Prompt for setting time"""
    user_id = callback_query.from_user.id
    logger.info(f"Setting user state for user {user_id}, is_admin: {is_admin(user_id)}")

    await callback_query.edit_message_text(
        "دزبندی کناں گال ءِ دیم دیگ ءِ وھدا بگوش: (پہ درور: 08:00)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("واترگ", callback_data="wod_back_to_settings")]
        ])
    )
    
    # Set user state to waiting for time input
    user_states[user_id] = "waiting_for_wod_time"
    logger.info(f"Current user_states: {user_states}")

# User states dictionary
user_states = {}

@Client.on_message(filters.text & ~filters.command(["word_of_day_settings", "send_word_of_day"]), group=-1)  # Change group to -1 for higher priority
async def handle_admin_input(client, message):
    """Handle admin input for settings"""
    user_id = message.from_user.id

    if is_admin(user_id) and user_id in user_states:
        if user_states[user_id] == "waiting_for_wod_time":
            # Check if the message looks like a time format (HH:MM)
            time_input = message.text.strip()

            # Log the time input for debugging
            logger.info(f"Received time input: {time_input}")
            
            if is_valid_time_format(time_input):
                # Update settings
                current_settings = load_settings()
                current_settings["time"] = time_input
                save_settings(current_settings)
                
                # Log the updated settings
                logger.info(f"Updated settings: {current_settings}")
                
                # Show confirmation and settings menu
                keyboard = [
                    [InlineKeyboardButton(f"⏰ وهد: {time_input}", callback_data="wod_set_time")],
                    [InlineKeyboardButton(f"📨 دیم دیگ په: {'چینل' if current_settings.get('target', DEFAULT_TARGET) == 'channel' else 'کارمرز کنوکاں'}", 
                                         callback_data="wod_toggle_target")]
                ]
                
                await message.reply(
                    f"⚙️ گال روچ ءِ کاربوج\n\n وھد بدل بوت په {time_input}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Clear user state
                del user_states[user_id]
                
                # Restart scheduler with new settings
                restart_scheduler(client)
                
                # Mark the message as handled to prevent further processing
                message.stop_propagation()
                return True
            else:
                await message.reply(
                    "وھد ءِ فارمیٹ رد انت. درستیں فارمیٹ: HH:MM (پہ درور: 08:00)"
                )
                # Mark the message as handled to prevent further processing
                message.stop_propagation()
                return True
    
    return False

@Client.on_callback_query(filters.regex(r"^wod_back_to_settings$"))  # Remove the group parameter
async def back_to_settings(client, callback_query):
    """Go back to settings menu"""
    user_id = callback_query.from_user.id
    
    # Clear user state if exists
    if user_id in user_states:
        del user_states[user_id]
    
    # Show settings menu
    current_settings = load_settings()
    keyboard = [
        [InlineKeyboardButton(f"⏰ وهد: {current_settings.get('time', DEFAULT_TIME)}", callback_data="wod_set_time")],
        [InlineKeyboardButton(f"📨  دیم دیگ په: {'چینل' if current_settings.get('target', DEFAULT_TARGET) == 'channel' else 'کارمرز کنوکاں'}", 
                             callback_data="wod_toggle_target")]
    ]
    
    await callback_query.edit_message_text(
       "⚙️ روچ گال ءِ کاربوج\n\nچیر ءِ بٹناں یکے ءَ بجن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Answer the callback query to remove the loading indicator
    await callback_query.answer()

def is_valid_time_format(time_str):
    """Validate time format (HH:MM)"""
    try:
        hours, minutes = time_str.split(":")
        hours = int(hours)
        minutes = int(minutes)
        return 0 <= hours < 24 and 0 <= minutes < 60
    except:
        return False

def restart_scheduler(app):
    """Restart the scheduler with new settings"""
    global scheduler_thread_running
    
    # Signal the current scheduler thread to stop
    scheduler_thread_running = False
    
    # Wait a bit for the thread to stop
    time.sleep(2)
    
    # Start a new scheduler thread
    start_scheduler(app)
    
    # Log the restart
    current_settings = load_settings()
    scheduled_time = current_settings.get("time", DEFAULT_TIME)
    logger.info(f"Word of day scheduler restarted with time: {scheduled_time}")
    
    # This will be called when settings change
    # The scheduler thread will pick up the new settings on its next iteration
    logger.info("Scheduler will be updated with new settings")
    
    # Clear existing jobs
    schedule.clear()
    
    # Load current settings
    current_settings = load_settings()
    scheduled_time = current_settings.get("time", DEFAULT_TIME)
    
    # Schedule the job
    schedule.every().day.at(scheduled_time).do(lambda: asyncio.run(send_word_of_day(app)))
    logger.info(f"Word of day rescheduled for {scheduled_time}")

# Start the scheduler in a separate thread
# In the start_scheduler function
def start_scheduler(app):
    """Start the scheduler thread"""
    global scheduler_thread, scheduler_thread_running
    
    # If a scheduler is already running, don't start another one
    if scheduler_thread_running and scheduler_thread and scheduler_thread.is_alive():
        logger.info("Scheduler already running, not starting a new one")
        return
    
    # Make sure the flag is reset
    scheduler_thread_running = False
    time.sleep(1)  # Give any existing thread time to stop
    
    # Start a new thread
    scheduler_thread_running = True
    scheduler_thread = threading.Thread(target=run_scheduler, args=(app,))
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logger.info("Word of day scheduler started")


@Client.on_message(filters.command("check_wod_scheduler") & filters.user(admin_id), group=0)
async def check_scheduler(client, message):
    """Check the status of the word of day scheduler"""
    global scheduler_thread, scheduler_thread_running
    
    current_settings = load_settings()
    scheduled_time = current_settings.get("time", DEFAULT_TIME)
    target = current_settings.get("target", DEFAULT_TARGET)
    
    status = "Running" if scheduler_thread_running and scheduler_thread and scheduler_thread.is_alive() else "Not running"
    
    next_run = None
    for job in schedule.jobs:
        next_run = job.next_run
        break
    
    next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "Not scheduled"
    
    await message.reply(
        f"Word of day scheduler status:\n"
        f"- Status: {status}\n"
        f"- Scheduled time: {scheduled_time}\n"
        f"- Target: {'Channel' if target == 'channel' else 'Users'}\n"
        f"- Next run: {next_run_str}"
    )