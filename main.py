from pyrogram import Client
from environs import Env
from bot_config import SayadGanjBotConfig
import logging

# configure plugins
plugins = dict(root="plugins")

# read .env file
config = SayadGanjBotConfig()

api_id = config.api_id
api_hash = config.api_hash
token = config.token

# Client instance
bot = Client(
    name="sayad_ganj",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=token,
    plugins=plugins,
)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    bot.run()