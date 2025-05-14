from pyrogram import Client, filters
from pyrogram.types import Message
from models.users import User, SearchHistory
from models.words import SayadGanj
import os
from dotenv import load_dotenv
import logging
from collections import Counter
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import jdatetime

# Load environment variables
load_dotenv()
admin_id = int(os.getenv('ADMIN_ID', 0))

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("stats") & filters.user(admin_id))
async def show_stats(client: Client, message: Message):
    """Show various statistics about the bot usage"""
    await message.reply("در حال تولید آمار...")
    
    # Basic stats
    total_users = User.select().count()
    total_words = SayadGanj.select().count()
    total_searches = SearchHistory.select().count()
    
    # Get active users in the last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")
    active_users = SearchHistory.select(SearchHistory.user).where(
        SearchHistory.search_date >= week_ago
    ).distinct().count()
    
    # Most searched words
    most_searched = Counter()
    for search in SearchHistory.select(SearchHistory.search_term):
        most_searched[search.search_term] += 1
    
    top_searches = most_searched.most_common(10)
    top_searches_text = "\n".join([f"{i+1}. {word} - {count} بار" for i, (word, count) in enumerate(top_searches)])
    
    # Generate stats text
    stats_text = f"""
📊 **آمار ربات**

👥 کاربران کل: {total_users}
📚 کلمات فرهنگ لغت: {total_words}
🔍 جستجوهای کل: {total_searches}
⚡ کاربران فعال (7 روز): {active_users}

🔝 **کلمات پرجستجو**:
{top_searches_text}
    """
    
    await message.reply(stats_text)
    
    # Generate and send a graph of searches over time
    await generate_search_graph(client, message)

async def generate_search_graph(client, message):
    """Generate a graph of searches over time"""
    # Get searches from the last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y/%m/%d")
    
    # Count searches by date
    date_counts = Counter()
    for search in SearchHistory.select(SearchHistory.search_date).where(
        SearchHistory.search_date >= thirty_days_ago
    ):
        date_counts[search.search_date] += 1
    
    # Sort by date
    dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in dates]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, counts)
    plt.title('جستجوها در طول زمان (30 روز گذشته)')
    plt.xlabel('تاریخ')
    plt.ylabel('تعداد جستجوها')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Send the image
    await client.send_photo(
        chat_id=message.chat.id,
        photo=buf,
        caption="فعالیت جستجو در 30 روز گذشته"
    )