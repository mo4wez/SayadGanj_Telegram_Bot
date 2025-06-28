from pyrogram import Client
from bot_config import SayadGanjBotConfig
import pyromod
import logging
import configparser

# configure plugins
plugins = dict(root="plugins")

# read .env file
config = SayadGanjBotConfig()

api_id = config.api_id
api_hash = config.api_hash
token = config.token

# read proxy file
proxy_config = configparser.ConfigParser()
proxy_config.read('proxy.ini')

proxy = {
    "scheme": proxy_config.get('proxy', 'scheme'),
    "hostname": proxy_config.get('proxy', 'hostname'),
    "port": proxy_config.getint('proxy', 'port'),
}

# Client instance
bot = Client(
    name="sayad_ganj",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=token,
    plugins=plugins,
    # proxy=proxy
)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    from plugins.word_of_day import start_scheduler
    start_scheduler(bot)
    bot.run()