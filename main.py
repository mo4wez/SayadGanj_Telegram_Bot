from pyrogram import Client
from environs import Env

# configure plugins
plugins = dict(root="plugins")

# read .env file
env = Env()
env.read_env()

api_id = env("API_ID")
api_hash = env("API_HASH")
token = env("TOKEN")

# Client instance
bot = Client(
    name="sayad_ganj",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=token,
    plugins=plugins,
)

if __name__ == '__main__':
    bot.run()