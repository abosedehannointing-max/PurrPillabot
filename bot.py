import asyncio
import os
import re
from openai import AsyncOpenAI

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    exit(1)

print(f"✅ Story Bot starting...")
print(f"✅ OpenAI: {'Connected' if OPENAI_API_KEY else 'Not configured'}")

# Initialize OpenAI client if API key provided
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Language translations
LANGUAGES = {
    'en': {
        'name': 'English',
        'welcome': "📖 *STORY GENERATOR BOT* 📖\n\nSimply send me a story title, and I'll create a beautiful story for you!\n\n*Examples:*\n`The Lost Key`\n`A Girl Who Found Magic`\n`The Last Rainbow`\n`Love in the Rain`\n\n*Commands:*\n/help - Show this message\n/language - Change language\n/genre [type] - Set genre (love, horror, adventure, fantasy)\n/status - Show current settings\n\n✨ *Just type any story title and I'll write it!* ✨",
        'help': "📖 *STORY GENERATOR BOT* 📖\n\nSimply send me a story title, and I'll create a beautiful story for you!\n\n*Examples:*\n`The Lost Key`\n`A Girl Who Found Magic`\n`The Last Rainbow`\n`Love in the Rain`\n\n*Commands:*\n/help - Show this message\n/language - Change language\n/genre [type] - Set genre (love, horror, adventure, fantasy)\n/status - Show current settings",
        'genre_list': "📖 *Current Genres Available:*\n\n• love - Romance stories\n• horror - Scary stories\n• adventure - Action/Adventure\n• fantasy - Magic/Fantasy\n• mystery - Detective/Mystery\n• inspirational - Uplifting stories\n\nUsage: `/genre love`",
        'genre_set': "✅ Genre set to: *{genre}*\n\nNow send me any story title!",
        'invalid_genre': "❌ Invalid genre. Choose: love, horror, adventure, fantasy, mystery, inspirational",
        'status': "📊 *Bot Status*\n\n🎨 Current genre: *{genre}*\n🤖 AI: {'Connected' if OPENAI_API_KEY else 'Not connected'}\n🌐 Language: {lang}\n\n✨ Send me any story title to generate a story!",
        'writing': "📖 Writing story about *{title}*... (AI is working)",
        'language_changed': "✅ Language changed to English!",
        'select_language': "🌐 *Select your language:*",
        'error': "❌ Error generating story: {error}"
    },
    'km': {
        'name': 'ភាសាខ្មែរ (Khmer)',
        'welcome': "📖 *BOT បង្កើតរឿង* 📖\n\nគ្រាន់តែផ្ញើចំណងជើងរឿងមកខ្ញុំ ខ្ញុំនឹងបង្កើតរឿងដ៏ស្រស់ស្អាតមួយសម្រាប់អ្នក!\n\n*ឧទាហរណ៍:*\n`កូនសោរដែលបាត់បង់`\n`ក្មេងស្រីដែលបានរកឃើញមន្តអាគម`\n`ឥន្ទធនូចុងក្រោយ`\n`ស្នេហាក្នុងភ្លៀង`\n\n*ពាក្យបញ្ជា:*\n/help - បង្ហាញសារនេះ\n/language - ផ្លាស់ប្តូរភាសា\n/genre [ប្រភេទ] - កំណត់ប្រភេទរឿង (ស្នេហា, ភ័យរន្ធត់, ដំណើរផ្សងព្រេង, រវើរវាយ)\n/status - បង្ហាញស្ថានភាពបច្ចុប្បន្ន\n\n✨ *គ្រាន់តែវាយបញ្ចូលចំណងជើងរឿង ខ្ញុំនឹងសរសេរវាឱ្យអ្នក!* ✨",
        'help': "📖 *BOT បង្កើតរឿង* 📖\n\nគ្រាន់តែផ្ញើចំណងជើងរឿងមកខ្ញុំ ខ្ញុំនឹងបង្កើតរឿងដ៏ស្រស់ស្អាតមួយសម្រាប់អ្នក!\n\n*ឧទាហរណ៍:*\n`កូនសោរដែលបាត់បង់`\n`ក្មេងស្រីដែលបានរកឃើញមន្តអាគម`\n`ឥន្ទធនូចុងក្រោយ`\n`ស្នេហាក្នុងភ្លៀង`\n\n*ពាក្យបញ្ជា:*\n/help - បង្ហាញសារនេះ\n/language - ផ្លាស់ប្តូរភាសា\n/genre [ប្រភេទ] - កំណត់ប្រភេទរឿង (ស្នេហា, ភ័យរន្ធត់, ដំណើរផ្សងព្រេង, រវើរវាយ)\n/status - បង្ហាញស្ថានភាពបច្ចុប្បន្ន",
        'genre_list': "📖 *ប្រភេទរឿងដែលមាន:*\n\n• love - រឿងស្នេហា\n• horror - រឿងភ័យរន្ធត់\n• adventure - រឿងដំណើរផ្សងព្រេង\n• fantasy - រឿងរវើរវាយ\n• mystery - រឿងអាថ៌កំបាំង\n• inspirational - រឿងបំផុសគំនិត\n\nការប្រើប្រាស់: `/genre love`",
        'genre_set': "✅ បានកំណត់ប្រភេទទៅ: *{genre}*\n\nឥឡូវផ្ញើចំណងជើងរឿងមកខ្ញុំ!",
        'invalid_genre': "❌ ប្រភេទមិនត្រឹមត្រូវ។ សូមជ្រើសរើស: love, horror, adventure, fantasy, mystery, inspirational",
        'status': "📊 *ស្ថានភាព Bot*\n\n🎨 ប្រភេទបច្ចុប្បន្ន: *{genre}*\n🤖 AI: {'Connected' if OPENAI_API_KEY else 'មិនទាន់ភ្ជាប់'}\n🌐 ភាសា: {lang}\n\n✨ ផ្ញើចំណងជើងរឿងណាមួយមកដើម្បីបង្កើតរឿង!",
        'writing': "📖 កំពុងសរសេររឿងអំពី *{title}*... (AI កំពុងដំណើរការ)",
        'language_changed': "✅ បានប្តូរភាសាទៅជាភាសាខ្មែរ!",
        'select_language': "🌐 *ជ្រើសរើសភាសារបស់អ្នក:*",
        'error': "❌ កំហុសក្នុងការបង្កើតរឿង: {error}"
    }
}

# ============ STORY GENERATOR ============
class StoryGenerator:
    
    @staticmethod
    async def generate_story(title: str, genre: str = "general", lang: str = "en") -> str:
        """Generate a story based on title using OpenAI"""
        
        if not openai_client:
            return "❌ OpenAI API key not configured. Please add OPENAI_API_KEY to environment variables."
        
        # Language-specific prompts
        prompts = {
            'en': f"""Write a short, engaging story based on this title: "{title}"

The story should be:
- Genre: {genre}
- Length: 300-500 words
- Have a clear beginning, middle, and end
- Be captivating and emotional
- Include a meaningful message or lesson

Format the story nicely with paragraphs, emojis, and a proper ending.""",
            
            'km': f"""សូមសរសេររឿងខ្លីមួយដោយផ្អែកលើចំណងជើងនេះ: "{title}"

រឿងគួរតែ:
- ប្រភេទ: {genre}
- ប្រវែង: ៣០០-៥០០ ពាក្យ
- មានចំណុចចាប់ផ្តើម កណ្តាល និងបញ្ចប់ច្បាស់លាស់
- ទាក់ទាញ និងរំជួលចិត្ត
- រួមបញ្ចូលសារឬមេរៀនដ៏មានអត្ថន័យ

រៀបចំរឿងឱ្យស្អាតជាមួយកថាខណ្ឌ រូបសញ្ញា និងការបញ្ចប់ដ៏សមរម្យ។"""
        }
        
        try:
            prompt = prompts.get(lang, prompts['en'])
            
            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional storyteller. Write beautiful, engaging stories that captivate readers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            story = response.choices[0].message.content
            
            # Add ending based on language
            if lang == 'km':
                story += f"\n\n✨ *ចប់* ✨\n\n#{title.replace(' ', '')} #រឿង #StoryTime"
            else:
                story += f"\n\n✨ *The End* ✨\n\n#{title.replace(' ', '')} #StoryTime"
            
            return story
            
        except Exception as e:
            return LANGUAGES[lang]['error'].format(error=str(e))

# ============ BOT ============
class StoryBot:
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        lang = context.user_data.get('language', 'en')
        
        # Create inline keyboard for language
        keyboard = [
            [InlineKeyboardButton("🌐 Change Language", callback_data="change_language")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            LANGUAGES[lang]['welcome'],
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get('language', 'en')
        await update.message.reply_text(LANGUAGES[lang]['help'], parse_mode="Markdown")
    
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show language selection menu"""
        keyboard = []
        for lang_code, lang_data in LANGUAGES.items():
            keyboard.append([InlineKeyboardButton(f"🌐 {lang_data['name']}", callback_data=f"lang_{lang_code}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            LANGUAGES['en']['select_language'],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def set_genre(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        args = context.args
        lang = context.user_data.get('language', 'en')
        
        if not args:
            await update.message.reply_text(
                LANGUAGES[lang]['genre_list'],
                parse_mode="Markdown"
            )
            return
        
        genre = args[0].lower()
        valid_genres = ["love", "horror", "adventure", "fantasy", "mystery", "inspirational"]
        
        if genre not in valid_genres:
            await update.message.reply_text(LANGUAGES[lang]['invalid_genre'])
            return
        
        # Store user genre preference
        context.user_data['genre'] = genre
        
        # Translate genre name for display
        genre_names = {
            'love': 'ស្នេហា' if lang == 'km' else 'Love',
            'horror': 'ភ័យរន្ធត់' if lang == 'km' else 'Horror',
            'adventure': 'ដំណើរផ្សងព្រេង' if lang == 'km' else 'Adventure',
            'fantasy': 'រវើរវាយ' if lang == 'km' else 'Fantasy',
            'mystery': 'អាថ៌កំបាំង' if lang == 'km' else 'Mystery',
            'inspirational': 'បំផុសគំនិត' if lang == 'km' else 'Inspirational'
        }
        
        display_genre = genre_names.get(genre, genre.capitalize())
        
        await update.message.reply_text(
            LANGUAGES[lang]['genre_set'].format(genre=display_genre),
            parse_mode="Markdown"
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        genre = context.user_data.get('genre', 'general')
        lang = context.user_data.get('language', 'en')
        
        # Translate genre for display
        genre_names = {
            'love': 'ស្នេហា' if lang == 'km' else 'Love',
            'horror': 'ភ័យរន្ធត់' if lang == 'km' else 'Horror',
            'adventure': 'ដំណើរផ្សងព្រេង' if lang == 'km' else 'Adventure',
            'fantasy': 'រវើរវាយ' if lang == 'km' else 'Fantasy',
            'mystery': 'អាថ៌កំបាំង' if lang == 'km' else 'Mystery',
            'inspirational': 'បំផុសគំនិត' if lang == 'km' else 'Inspirational',
            'general': 'ទូទៅ' if lang == 'km' else 'General'
        }
        
        display_genre = genre_names.get(genre, genre.capitalize())
        
        lang_name = 'ភាសាខ្មែរ' if lang == 'km' else 'English'
        
        await update.message.reply_text(
            LANGUAGES[lang]['status'].format(genre=display_genre, lang=lang_name),
            parse_mode="Markdown"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        title = update.message.text.strip()
        lang = context.user_data.get('language', 'en')
        
        # Skip if it's a command
        if title.startswith('/'):
            return
        
        # Get user's preferred genre
        genre = context.user_data.get('genre', 'general')
        
        # Send typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Send initial message
        status_msg = await update.message.reply_text(
            LANGUAGES[lang]['writing'].format(title=title),
            parse_mode="Markdown"
        )
        
        # Generate story
        story = await StoryGenerator.generate_story(title, genre, lang)
        
        # Edit the status message with the story
        await status_msg.edit_text(story, parse_mode="Markdown")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button presses"""
        query = update.callback_query
        await query.answer()
        
        # Handle language selection
        if query.data.startswith("lang_"):
            new_lang = query.data.replace("lang_", "")
            context.user_data['language'] = new_lang
            await query.edit_message_text(
                LANGUAGES[new_lang]['language_changed'],
                parse_mode='Markdown'
            )
        
        elif query.data == "change_language":
            keyboard = []
            for lang_code, lang_data in LANGUAGES.items():
                keyboard.append([InlineKeyboardButton(f"🌐 {lang_data['name']}", callback_data=f"lang_{lang_code}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                LANGUAGES['en']['select_language'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

# ============ MAIN ============
async def main():
    print("🚀 Starting Story Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot = StoryBot()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(CommandHandler("language", bot.language_command))
    application.add_handler(CommandHandler("genre", bot.set_genre))
    application.add_handler(CommandHandler("status", bot.status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    print("📡 Starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Story Bot is LIVE!")
    print("📖 Ready to generate stories!")
    print("🌐 Supported languages: English, Khmer")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    print("🌟 STORY BOT DEPLOYING...")
    asyncio.run(main())
