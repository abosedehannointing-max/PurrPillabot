import asyncio
import os
import re
from openai import AsyncOpenAI

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not BOT_TOKEN:
    print("❌ កំហុស: រកមិនឃើញ TELEGRAM_BOT_TOKEN!")
    exit(1)

print(f"✅ កំពុងចាប់ផ្តើម Bot បង្កើតរឿង...")
print(f"✅ OpenAI: {'បានភ្ជាប់' if OPENAI_API_KEY else 'មិនទាន់កំណត់រចនាសម្ព័ន្ធ'}")

# Initialize OpenAI client if API key provided
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ============ ប្រព័ន្ធបង្កើតរឿង ============
class StoryGenerator:
    
    @staticmethod
    async def generate_story(title: str, genre: str = "general") -> str:
        """បង្កើតរឿងដោយផ្អែកលើចំណងជើង ដោយប្រើ OpenAI"""
        
        if not openai_client:
            return "❌ មិនទាន់កំណត់ OpenAI API key ។ សូមបន្ថែម OPENAI_API_KEY ទៅក្នុងអថេរបរិស្ថាន។"
        
        # Genre translations
        genre_khmer = {
            'love': 'រឿងស្នេហា',
            'horror': 'រឿងភ័យរន្ធត់',
            'adventure': 'រឿងដំណើរផ្សងព្រេង',
            'fantasy': 'រឿងរវើរវាយ',
            'mystery': 'រឿងអាថ៌កំបាំង',
            'inspirational': 'រឿងបំផុសគំនិត',
            'general': 'រឿងទូទៅ'
        }
        
        genre_display = genre_khmer.get(genre, genre)
        
        try:
            prompt = f"""សូមសរសេររឿងខ្លីមួយដោយផ្អែកលើចំណងជើងនេះ: "{title}"

តម្រូវការរឿង:
- ប្រភេទ: {genre_display}
- ប្រវែង: ៣០០-៥០០ ពាក្យ
- មានចំណុចចាប់ផ្តើម កណ្តាល និងបញ្ចប់ច្បាស់លាស់
- គួរឱ្យចាប់អារម្មណ៍ និងទាក់ទាញ
- មានអត្ថន័យ ឬមេរៀនល្អៗ

សូមរៀបចំរឿងឱ្យស្អាត មានកថាខណ្ឌ រូបសញ្ញា និងការបញ្ចប់ដ៏សមរម្យ។
សរសេរជាភាសាខ្មែរឱ្យបានត្រឹមត្រូវ និងធម្មជាតិ។"""
            
            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "អ្នកគឺជាអ្នកនិទានរឿងអាជីព។ អ្នកសរសេររឿងដ៏ស្រស់ស្អាត ទាក់ទាញ និងធ្វើឱ្យអ្នកអានចាប់អារម្មណ៍។ សរសេរជាភាសាខ្មែរឱ្យបានត្រឹមត្រូវ។"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            story = response.choices[0].message.content
            story += f"\n\n✨ *ចប់* ✨\n\n#{title.replace(' ', '')} #រឿង #StoryTime"
            
            return story
            
        except Exception as e:
            return f"❌ កំហុសក្នុងការបង្កើតរឿង: {str(e)}"

# ============ BOT ============
class StoryBot:
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ពាក្យបញ្ជា /start - ចាប់ផ្តើម Bot"""
        welcome_text = """
📖 *BOT បង្កើតរឿង* 📖

សួស្តី! ខ្ញុំជា Bot បង្កើតរឿងដោយប្រើបញ្ញាសិប្បនិម្មិត (AI)។

*របៀបប្រើប្រាស់៖*
គ្រាន់តែផ្ញើចំណងជើងរឿងមកខ្ញុំ ខ្ញុំនឹងបង្កើតរឿងដ៏ស្រស់ស្អាតមួយសម្រាប់អ្នក!

*ឧទាហរណ៍ចំណងជើង៖*
• `កូនសោរដែលបាត់បង់`
• `ក្មេងស្រីដែលបានរកឃើញមន្តអាគម`
• `ឥន្ទធនូចុងក្រោយ`
• `ស្នេហាក្នុងភ្លៀង`
• `អ្នកចម្បាំងទឹកកក`

*ពាក្យបញ្ជាផ្សេងទៀត៖*
/help - បង្ហាញជំនួយ
/genre - កំណត់ប្រភេទរឿង
/status - បង្ហាញស្ថានភាពបច្ចុប្បន្ន

✨ *សាកល្បងឥឡូវនេះ - គ្រាន់តែវាយបញ្ចូលចំណងជើងរឿង!* ✨
"""
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ពាក្យបញ្ជា /help - បង្ហាញជំនួយ"""
        help_text = """
📖 *ជំនួយប្រើប្រាស់ Bot* 📖

*របៀបប្រើប្រាស់៖*
1. វាយបញ្ចូលចំណងជើងរឿងណាមួយ
2. Bot នឹងបង្កើតរឿងដោយស្វ័យប្រវត្តិ
3. រីករាយជាមួយរឿងដែលបានបង្កើត!

*ពាក្យបញ្ជាទាំងអស់៖*
/start - ចាប់ផ្តើម Bot
/help - បង្ហាញជំនួយនេះ
/genre - កំណត់ប្រភេទរឿង
/status - បង្ហាញស្ថានភាពបច្ចុប្បន្ន

*ឧទាហរណ៍ចំណងជើងរឿង៖*
• ដំណើរផ្សងព្រេងក្នុងព្រៃ
• ក្តីស្រមៃរបស់ក្មេងកំព្រា
• ស្នេហ៍ឆ្លងកាល
• អាថ៌កំបាំងប្រាសាទបុរាណ
• ទេវតាអាណាព្យាបាល

💡 *ការណែនាំ៖* ចំណងជើងកាន់តែលម្អិត រឿងនឹងកាន់តែល្អ!
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def set_genre(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ពាក្យបញ្ជា /genre - កំណត់ប្រភេទរឿង"""
        args = context.args
        
        # Genre keyboard
        genre_keyboard = [
            [InlineKeyboardButton("💖 ស្នេហា", callback_data="genre_love")],
            [InlineKeyboardButton("👻 ភ័យរន្ធត់", callback_data="genre_horror")],
            [InlineKeyboardButton("⚔️ ដំណើរផ្សងព្រេង", callback_data="genre_adventure")],
            [InlineKeyboardButton("✨ រវើរវាយ", callback_data="genre_fantasy")],
            [InlineKeyboardButton("🕵️ អាថ៌កំបាំង", callback_data="genre_mystery")],
            [InlineKeyboardButton("🌟 បំផុសគំនិត", callback_data="genre_inspirational")],
            [InlineKeyboardButton("📖 ទូទៅ", callback_data="genre_general")]
        ]
        reply_markup = InlineKeyboardMarkup(genre_keyboard)
        
        if not args:
            await update.message.reply_text(
                "📖 *ជ្រើសរើសប្រភេទរឿងដែលអ្នកចូលចិត្ត៖*\n\nចុចលើប៊ូតុងខាងក្រោម៖",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # If user types genre manually
        genre = args[0].lower()
        valid_genres = {
            "love": "💖 ស្នេហា",
            "horror": "👻 ភ័យរន្ធត់", 
            "adventure": "⚔️ ដំណើរផ្សងព្រេង",
            "fantasy": "✨ រវើរវាយ",
            "mystery": "🕵️ អាថ៌កំបាំង",
            "inspirational": "🌟 បំផុសគំនិត",
            "general": "📖 ទូទៅ"
        }
        
        if genre not in valid_genres:
            await update.message.reply_text(
                f"❌ ប្រភេទ '{genre}' មិនត្រឹមត្រូវទេ។\n\n"
                f"ប្រភេទដែលមាន៖ love, horror, adventure, fantasy, mystery, inspirational, general"
            )
            return
        
        context.user_data['genre'] = genre
        await update.message.reply_text(
            f"✅ បានកំណត់ប្រភេទរឿងទៅ: *{valid_genres[genre]}*\n\n"
            f"ឥឡូវអ្នកអាចផ្ញើចំណងជើងរឿងមកខ្ញុំបាន!",
            parse_mode="Markdown"
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ពាក្យបញ្ជា /status - បង្ហាញស្ថានភាព"""
        genre = context.user_data.get('genre', 'general')
        
        genre_names = {
            'love': '💖 ស្នេហា',
            'horror': '👻 ភ័យរន្ធត់',
            'adventure': '⚔️ ដំណើរផ្សងព្រេង',
            'fantasy': '✨ រវើរវាយ',
            'mystery': '🕵️ អាថ៌កំបាំង',
            'inspirational': '🌟 បំផុសគំនិត',
            'general': '📖 ទូទៅ'
        }
        
        display_genre = genre_names.get(genre, '📖 ទូទៅ')
        ai_status = 'បានភ្ជាប់ ✓' if OPENAI_API_KEY else 'មិនទាន់ភ្ជាប់ ✗'
        
        status_text = f"""
📊 *ស្ថានភាព Bot*

━━━━━━━━━━━━━━━━━━
🎨 *ប្រភេទរឿងបច្ចុប្បន្ន:* {display_genre}

🤖 *ស្ថានភាព AI:* {ai_status}

📝 *ចំនួនរឿងដែលបានបង្កើត:* {context.user_data.get('story_count', 0)}

━━━━━━━━━━━━━━━━━━

✨ *ផ្ញើចំណងជើងរឿងណាមួយមក ដើម្បីបង្កើតរឿងថ្មី!*
"""
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ដំណើរការសារពីអ្នកប្រើប្រាស់"""
        title = update.message.text.strip()
        
        # Skip if it's a command
        if title.startswith('/'):
            return
        
        # Update story count
        story_count = context.user_data.get('story_count', 0)
        context.user_data['story_count'] = story_count + 1
        
        # Get user's preferred genre
        genre = context.user_data.get('genre', 'general')
        
        # Send typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Send initial message
        status_msg = await update.message.reply_text(
            f"📖 *កំពុងសរសេររឿងអំពី* \"{title}\" *...*\n\n"
            f"🤖 AI កំពុងបង្កើតរឿងដ៏ស្រស់ស្អាតសម្រាប់អ្នក (សូមរងចាំបន្តិច)",
            parse_mode="Markdown"
        )
        
        # Generate story
        story = await StoryGenerator.generate_story(title, genre)
        
        # Edit the status message with the story
        await status_msg.edit_text(story, parse_mode="Markdown")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ដំណើរការការចុចប៊ូតុង"""
        query = update.callback_query
        await query.answer()
        
        # Handle genre selection from buttons
        if query.data.startswith("genre_"):
            genre = query.data.replace("genre_", "")
            context.user_data['genre'] = genre
            
            genre_names = {
                'love': '💖 ស្នេហា',
                'horror': '👻 ភ័យរន្ធត់',
                'adventure': '⚔️ ដំណើរផ្សងព្រេង',
                'fantasy': '✨ រវើរវាយ',
                'mystery': '🕵️ អាថ៌កំបាំង',
                'inspirational': '🌟 បំផុសគំនិត',
                'general': '📖 ទូទៅ'
            }
            
            display_genre = genre_names.get(genre, '📖 ទូទៅ')
            
            await query.edit_message_text(
                f"✅ *បានកំណត់ប្រភេទរឿងទៅ:* {display_genre}\n\n"
                f"ឥឡូវអ្នកអាចផ្ញើចំណងជើងរឿងមកខ្ញុំបាន!\n\n"
                f"💡 *ឧទាហរណ៍:* \"ដំណើរផ្សងព្រេងក្នុងព្រៃ\"",
                parse_mode="Markdown"
            )

# ============ MAIN ============
async def main():
    print("🚀 កំពុងចាប់ផ្តើម Bot បង្កើតរឿង...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot = StoryBot()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(CommandHandler("genre", bot.set_genre))
    application.add_handler(CommandHandler("status", bot.status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    print("📡 កំពុងភ្ជាប់ទៅ Telegram...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Bot បង្កើតរឿងបានដំណើរការដោយជោគជ័យ!")
    print("📖 រួចរាល់ក្នុងការបង្កើតរឿងជាភាសាខ្មែរ!")
    print("💡 គ្រាន់តែផ្ញើចំណងជើងរឿងមក Bot!")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    print("🌟 កំពុងដាក់ពង្រាយ Bot...")
    asyncio.run(main())
