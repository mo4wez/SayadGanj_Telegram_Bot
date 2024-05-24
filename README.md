# SayadGanj Balochi Dictionary Telegram Bot

This is a Telegram bot developed using Pyrogram and SQLite to provide a Balochi dictionary service. Users can access translations and meanings of words in the Balochi language through this bot.

## Features

- **Balochi Dictionary:** Look up words in Balochi language with their translations and meanings.
- **SQLite Database:** Utilizes an SQLite database to store and retrieve word entries efficiently.
- **Pyrogram Framework:** Built on the Pyrogram framework for easy integration with Telegram's Bot API.

## SayadGanj Bot
![sayadganj](https://github.com/mo4wez/SayadGanj_Telegram_Bot/assets/44638454/bfed4aa7-80a0-4c66-b7a4-ed0e176b9ef3)

## See it in telegram
```
@sayadganj_bot
```

## Requirements

- Python 3.9 or higher
- Pyrogram
- TgCrypto
- pyromod
- peewee

## Installation

1. **Clone this repository:**

    ```
    git clone https://github.com/mo4wez/SayadGanj_Telegram_Bot.git
    ```

2. **Navigate to the project directory:**

    ```
    cd SayadGanj_Telegram_Bot
    ```

3. **Install dependencies using Pipenv:**

    ```
    virtualenv venv
    ```

3. **Install dependencies:**

    ```
    pip install -r requirements.txt
    ```


4. **Obtain Telegram API credentials from [Telegram's BotFather](https://core.telegram.org/bots#6-botfather).**


5. **Create a .env file in the project directory and add your environment variables:**

    ```plaintext
    API_ID=YOUR_API_ID
    API_HASH=YOUR_API_HASH
    TOKEN=YOUR_BOT_TOKEN
    ADMIN_ID=YOUR_CHAT_ID
    ```
6. **Main Database:**

   You will need a database named wordbook.db for searching words.
   
7. **Run the bot:**

    ```
    python main.py
    ```

## Usage

- **Text Filters:** After initiating the bot with the `/start` command, you can simply send a text message to search for words within the conversation.
- **Inline Search:** Use the `/search` command to perform inline word searches directly in the chat.

### Inline Search

1. Begin a message with the bot by typing `@your_bot_username`.
2. Use the command `/search <word>` to look up a word in the Balochi dictionary inline.
3. The bot will display word suggestions matching your query, along with their translations and meanings.

### Text Filters

1. Start the bot by sending the `/start` command in the chat.
2. Subsequently, if you send any text message containing a word, the bot will automatically detect the word and provide its translation and meaning if found in the dictionary.

## Contributing

Contributions are welcome! If you want to contribute to this project, feel free to fork the repository and submit a pull request with your changes.
