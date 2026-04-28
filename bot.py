import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Story prompt patterns
STORY_PROMPTS = {
    'fantasy': [
        "In a world where {title} controls reality, a young hero discovers they have the power to...",
        "The ancient prophecy spoke of {title}, but no one expected it to arrive in the form of...",
        "When {title} appears every 1000 years, society must choose between...",
    ],
    'sci-fi': [
        "The AI system called '{title}' has just become self-aware and its first action is to...",
        "In 2150, {title} is the last hope for humanity, but at what cost?",
        "A glitch in {title} causes reality to rewrite itself, leading to...",
    ],
    'mystery': [
        "The disappearance of {title} has baffled detectives for decades, until now...",
        "Everyone in town knows about {title}, but no one speaks of it. Tonight, that changes because...",
        "The {title} secret society has operated in shadows for centuries. Today, someone exposed them by...",
    ],
    'romance': [
        "Two strangers meet because of {title}, but neither realizes they were destined to...",
        "{title} brought them together, but can it also tear them apart?",
        "Love was never part of the plan for {title}, yet here we are...",
    ],
    'horror': [
        "They said {title} was just a legend, until people started disappearing...",
        "The {title} curse awakens every generation. This time, it's different because...",
        "You shouldn't have searched for {title}. Now it knows where you live...",
    ]
}

class StoryBot:
    def __init__(self):
        self.genres = list(STORY_PROMPTS.keys())
    
    def generate_story_prompt(self, title, genre=None):
        """Generate a story prompt based on title and genre"""
        if not genre or genre not in STORY_PROMPTS:
            genre = random.choice(self.genres)
        
        template = random.choice(STORY_PROMPTS[genre])
        prompt = template.replace('{title}', title)
        
        return f"📖 *Genre: {genre.capitalize()}*\n\n{prompt}\n\n✨ *Your Story Title:* {title}\n\n💡 Tip: Add characters, setting, or conflict to expand this prompt!"

# Initialize bot
story_bot = StoryBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued"""
    welcome_message = (
        "🎭 *Welcome to Story Prompt Generator Bot!*\n\n"
        "I can help you turn any title into a creative story prompt.\n\n"
        "*How to use:*\n"
        "1. Send me any title (e.g., 'The Lost Kingdom')\n"
        "2. Choose a genre for your prompt\n"
        "3. Get a unique story prompt instantly!\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/genres - Show available genres\n"
        "/random - Generate random story prompt\n\n"
        "Try it now - just send me a title!"
    )
    
    keyboard = [
        [InlineKeyboardButton("✨ Try Example", callback_data="example")],
        [InlineKeyboardButton("📚 View Genres", callback_data="genres")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = (
        "*📖 Help Guide*\n\n"
        "*Basic Usage:*\n"
        "Just send any title, and I'll ask for genre preferences!\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/generate <title> - Generate prompt for specific title\n"
        "/genres - List all available genres\n"
        "/random - Generate random story prompt\n"
        "/help - Show this help\n\n"
        "*Example:*\n"
        "Send: 'The Midnight Library'\n"
        "Then choose a genre like 'fantasy' or 'mystery'"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_genres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available genres"""
    genres_text = "*Available Genres:*\n\n"
    for genre in story_bot.genres:
        genres_text += f"🎭 *{genre.capitalize()}*\n"
    
    keyboard = []
    for genre in story_bot.genres:
        keyboard.append([InlineKeyboardButton(f"📖 {genre.capitalize()}", callback_data=f"genre_{genre}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(genres_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input as a title"""
    title = update.message.text.strip()
    context.user_data['current_title'] = title
    
    keyboard = []
    for genre in story_bot.genres:
        keyboard.append([InlineKeyboardButton(f"📖 {genre.capitalize()}", callback_data=f"genre_{genre}")])
    
    keyboard.append([InlineKeyboardButton("🎲 Random Genre", callback_data="random_genre")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎯 *Title:* {title}\n\nChoose a genre for your story prompt:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "example":
        example_title = "The Whispering Shadows"
        context.user_data['current_title'] = example_title
        
        keyboard = []
        for genre in story_bot.genres:
            keyboard.append([InlineKeyboardButton(f"📖 {genre.capitalize()}", callback_data=f"genre_{genre}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎯 *Example Title:* {example_title}\n\nChoose a genre:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "genres":
        genres_text = "*Available Genres:*\n\n"
        for genre in story_bot.genres:
            genres_text += f"🎭 *{genre.capitalize()}* - Perfect for {genre} stories\n\n"
        await query.edit_message_text(genres_text, parse_mode='Markdown')
    
    elif query.data == "random_genre":
        title = context.user_data.get('current_title', 'Mysterious Adventure')
        genre = random.choice(story_bot.genres)
        prompt = story_bot.generate_story_prompt(title, genre)
        
        keyboard = [[InlineKeyboardButton("🎲 Another Prompt", callback_data=f"regenerate_{title}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(prompt, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data.startswith("genre_"):
        genre = query.data.replace("genre_", "")
        title = context.user_data.get('current_title', 'Untitled Story')
        prompt = story_bot.generate_story_prompt(title, genre)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Regenerate", callback_data=f"regenerate_{title}")],
            [InlineKeyboardButton("📖 Different Genre", callback_data="genre_select")],
            [InlineKeyboardButton("✨ Random Prompt", callback_data="random_prompt")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(prompt, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data.startswith("regenerate_"):
        title = query.data.replace("regenerate_", "")
        context.user_data['current_title'] = title
        
        keyboard = []
        for genre in story_bot.genres:
            keyboard.append([InlineKeyboardButton(f"📖 {genre.capitalize()}", callback_data=f"genre_{genre}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎯 *Title:* {title}\n\nChoose a genre for a new prompt:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "genre_select":
        title = context.user_data.get('current_title', 'Story')
        
        keyboard = []
        for genre in story_bot.genres:
            keyboard.append([InlineKeyboardButton(f"📖 {genre.capitalize()}", callback_data=f"genre_{genre}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎯 *Title:* {title}\n\nChoose a different genre:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "random_prompt":
        random_titles = [
            "The Last Guardian", "Echoes of Tomorrow", "Whispers in the Dark",
            "The Forgotten City", "Beyond the Stars", "Secrets of the Deep"
        ]
        random_title = random.choice(random_titles)
        random_genre = random.choice(story_bot.genres)
        prompt = story_bot.generate_story_prompt(random_title, random_genre)
        
        keyboard = [[InlineKeyboardButton("🎲 Another Random", callback_data="random_prompt")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎲 *Random Story Prompt*\n\n{prompt}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate command"""
    if context.args:
        title = ' '.join(context.args)
        context.user_data['current_title'] = title
        
        keyboard = []
        for genre in story_bot.genres:
            keyboard.append([InlineKeyboardButton(f"📖 {genre.capitalize()}", callback_data=f"genre_{genre}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎯 *Title:* {title}\n\nChoose a genre:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "Please provide a title.\nExample: `/generate The Lost Kingdom`",
            parse_mode='Markdown'
        )

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate random story prompt"""
    random_titles = [
        "The Crystal Cave", "Midnight Express", "Starlight Chronicles",
        "The Whispering Woods", "Digital Dreams", "The Phantom's Curse",
        "Eternal Sunset", "The Clockwork Heart"
    ]
    title = random.choice(random_titles)
    genre = random.choice(story_bot.genres)
    prompt = story_bot.generate_story_prompt(title, genre)
    
    await update.message.reply_text(
        f"🎲 *Random Story Prompt*\n\n{prompt}\n\nTry /generate to create your own!",
        parse_mode='Markdown'
    )

def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN found! Please set it in environment variables")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("genres", show_genres))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("random", random_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
