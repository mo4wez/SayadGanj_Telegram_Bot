import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from models.words import SayadGanj
import logging
from filters.join_checker_filter import is_joined_filter

from constants.bot_messages import QUIZ_INTRO, QUIZ_QUESTION, QUIZ_RESULT, QUIZ_WRONG, QUIZ_CORRECT

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active quizzes
active_quizzes = {}

@Client.on_message(filters.command("quiz") & filters.private & is_joined_filter, group=5)
async def start_quiz(client: Client, message: Message):
    """Start a new word quiz"""
    chat_id = message.chat.id
    
    # Send introduction message
    await message.reply(QUIZ_INTRO)
    
    # Start the quiz with the first question
    await send_quiz_question(client, chat_id)

async def send_quiz_question(client, chat_id, question_number=1, score=0, total_questions=5):
    """Send a quiz question to the user"""
    if question_number > total_questions:
        # Quiz is complete
        await send_quiz_results(client, chat_id, score, total_questions)
        return
    
    # Get random words for the quiz
    total_words = SayadGanj.select().count()
    correct_word_id = random.randint(1, total_words)
    
    try:
        correct_word = SayadGanj.get(SayadGanj.id == correct_word_id)
        
        # Clean the definition by removing the word and its pronunciation
        definition = correct_word.definition
        
        # Remove the word, any characters between ":" and "(", and the pronunciation in parentheses
        import re
        cleaned_definition = re.sub(r'^[^:]+:\s*[^(]*\([^)]+\)\s*', '', definition)
        
        # Get 3 random incorrect options
        wrong_options = []
        while len(wrong_options) < 3:
            wrong_id = random.randint(1, total_words)
            if wrong_id != correct_word_id:
                try:
                    wrong_word = SayadGanj.get(SayadGanj.id == wrong_id)
                    if wrong_word.full_word not in wrong_options:
                        wrong_options.append(wrong_word.full_word)
                except:
                    pass
        
        # Create options with the correct answer and 3 wrong answers
        options = wrong_options + [correct_word.full_word]
        random.shuffle(options)
        
        # Create keyboard with options
        keyboard = []
        for i, option in enumerate(options):
            keyboard.append([
                InlineKeyboardButton(
                    option, 
                    callback_data=f"quiz_{question_number}_{score}_{i}_{options.index(correct_word.full_word)}"
                )
            ])
        
        # Store the quiz state
        active_quizzes[chat_id] = {
            'question': question_number,
            'score': score,
            'correct_word': correct_word,
            'options': options
        }
        
        # Send the question
        await client.send_message(
            chat_id=chat_id,
            text=QUIZ_QUESTION.format(
                number=question_number,
                total=total_questions,
                definition=cleaned_definition
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in quiz: {e}")
        await client.send_message(
            chat_id=chat_id,
            text="متأسفانه در ایجاد سؤال آزمون خطایی رخ داد. لطفا دوباره تلاش کنید."
        )

async def send_quiz_results(client, chat_id, score, total_questions):
    """Send the final quiz results"""
    # Calculate percentage
    percentage = (score / total_questions) * 100
    
    # Send results message
    await client.send_message(
        chat_id=chat_id,
        text=QUIZ_RESULT.format(
            score=score,
            total=total_questions,
            percentage=percentage
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("پدا لیب کن", callback_data="quiz_restart")]
        ])
    )
    
    # Clear the quiz state
    if chat_id in active_quizzes:
        del active_quizzes[chat_id]

@Client.on_callback_query(filters.regex(r"^quiz_"))
async def handle_quiz_callback(client: Client, callback_query: CallbackQuery):
    """Handle quiz button callbacks"""
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    if data == "quiz_restart":
        # Restart the quiz
        await callback_query.message.delete()
        await send_quiz_question(client, chat_id)
        return
    
    # Parse the callback data
    parts = data.split("_")
    if len(parts) >= 5:
        question_number = int(parts[1])
        score = int(parts[2])
        selected_option = int(parts[3])
        correct_option = int(parts[4])
        
        # Check if the answer is correct
        if selected_option == correct_option:
            # Correct answer
            await callback_query.answer(QUIZ_CORRECT, show_alert=True)
            score += 1
        else:
            # Wrong answer
            correct_word = active_quizzes[chat_id]['correct_word'].full_word
            await callback_query.answer(QUIZ_WRONG.format(word=correct_word), show_alert=True)
        
        # Move to the next question
        await callback_query.message.delete()
        await send_quiz_question(client, chat_id, question_number + 1, score)