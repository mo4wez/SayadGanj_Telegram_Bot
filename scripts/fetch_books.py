import asyncio
import json
import os
import re
import configparser
from pyrogram import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# read proxy file
proxy_config = configparser.ConfigParser()
proxy_config.read('proxy.ini')

proxy = {
    "scheme": proxy_config.get('proxy', 'scheme'),
    "hostname": proxy_config.get('proxy', 'hostname'),
    "port": proxy_config.getint('proxy', 'port'),
}

# Get API credentials from environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
channel_username = "sayadganjarc"  # Your channel username

# Path to book info file
book_info_path = "book_info.json"

# Regular expressions to extract book name and author
book_name_pattern = re.compile(r'📚\s*(.*?)(?:\n|$)')
author_pattern = re.compile(r'📝\s*(.*?)(?:\n|$)')

async def fetch_books():
    """Fetch books from the channel and update book_info.json"""
    # Initialize the client
    async with Client("book_fetcher", api_id, api_hash, bot_token=bot_token, proxy=proxy) as app:
        print("Connected to Telegram. Fetching messages...")
        
        # Load existing book info if available
        if os.path.exists(book_info_path):
            with open(book_info_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
        else:
            book_data = {"books": []}
        
        # Create a set of existing IDs for quick lookup
        existing_ids = {book["id"] for book in book_data["books"]}
        
        # Get messages from the channel (adjust the range as needed)
        # Start from a reasonable message ID and get the last 100 messages
        messages = await app.get_messages(channel_username, list(range(1, 100)))
        
        # Process each message
        for message in messages:
            # Skip messages without documents or media
            if not message.document and not message.media:
                continue
            
            # Skip if we already have this message ID
            if message.id in existing_ids:
                continue
            
            # Check if the message has a caption
            if message.caption:
                # Extract book name and author from caption
                book_name_match = book_name_pattern.search(message.caption)
                author_match = author_pattern.search(message.caption)
                
                book_name = book_name_match.group(1).strip() if book_name_match else "Unknown Book"
                author = author_match.group(1).strip() if author_match else "Unknown Author"
                
                # Add book to the data
                book_data["books"].append({
                    "id": message.id,
                    "name": book_name,
                    "author": author,
                    "description": f"By {author}"
                })
                
                print(f"Found book: {book_name} by {author} (ID: {message.id})")
        
        # Save updated book data
        with open(book_info_path, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)
        
        print(f"Book data saved to {book_info_path}")

if __name__ == "__main__":
    asyncio.run(fetch_books())