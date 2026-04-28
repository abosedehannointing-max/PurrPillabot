import asyncio
import os
import re
from openai import AsyncOpenAI

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    exit(1)

print(f"✅ Story Bot starting...")
print(f"✅ OpenAI: {'Connected' if OPENAI_API_KEY else 'Not configured'}")

# Initialize OpenAI client if API key provided
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ============ STORY GENERATOR ============
class StoryGenerator:
    
    @staticmethod
    async def generate_story(title: str, genre: str = "general") -> str:
        """Generate a story based on title using OpenAI"""
        
        if not openai_client:
            return "❌ OpenAI API key not configured. Please add OPENAI_API_KEY to environment variables."
        
        try:
            prompt = f"""Write a short, engaging story based on this title: "{title}"

The story should be:
- Genre: {genre}
- Length: 300-500 words
- Have a clear beginning, middle, and end
- Be captivating and emotional
- Include a meaningful message or lesson

Format the story nicely with paragraphs, emojis, and a proper ending."""
            
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
            story += f"\n\n✨ *The End* ✨\n\n#{title.replace(' ', '')} #StoryTime"
            
            return story
            
        except Exception as e:
            return f"❌ Error generating story: {str(e)}"

# ============ BOT ============
class StoryBot:
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 *STORY GENERATOR BOT* 📖\n\n"
            "Simply send me a story title, and I'll create a beautiful story for you!\n\n"
            "*Examples:*\n"
            "`The Lost Key`\n"
            "`A Girl Who Found Magic`\n"
            "`The Last Rainbow`\n"
            "`Love in the Rain`\n\n"
            "*Commands:*\n"
            "/help - Show this message\n"
            "/genre [type] - Set genre (love, horror, adventure, fantasy)\n"
            "/status - Show current settings\n\n"
            "✨ *Just type any story title and I'll write it!* ✨",
            parse_mode="Markdown"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)
    
    async def set_genre(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "📖 *Current Genres Available:*\n\n"
                "• love - Romance stories\n"
                "• horror - Scary stories\n"
                "• adventure - Action/Adventure\n"
                "• fantasy - Magic/Fantasy\n"
                "• mystery - Detective/Mystery\n"
                "• inspirational - Uplifting stories\n\n"
                "Usage: `/genre love`",
                parse_mode="Markdown"
            )
            return
        
        genre = args[0].lower()
        valid_genres = ["love", "horror", "adventure", "fantasy", "mystery", "inspirational"]
        
        if genre not in valid_genres:
            await update.message.reply_text(f"❌ Invalid genre. Choose: {', '.join(valid_genres)}")
            return
        
        # Store user genre preference
        if not hasattr(context.user_data, 'genre'):
            context.user_data['genre'] = {}
        context.user_data['genre'] = genre
        
        await update.message.reply_text(f"✅ Genre set to: *{genre.capitalize()}*\n\nNow send me any story title!", parse_mode="Markdown")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        genre = context.user_data.get('genre', 'general')
        
        await update.message.reply_text(
            f"📊 *Bot Status*\n\n"
            f"🎨 Current genre: *{genre.capitalize()}*\n"
            f"🤖 AI: {'Connected' if OPENAI_API_KEY else 'Not connected'}\n\n"
            f"✨ Send me any story title to generate a story!",
            parse_mode="Markdown"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        title = update.message.text.strip()
        
        # Skip if it's a command
        if title.startswith('/'):
            return
        
        # Get user's preferred genre
        genre = context.user_data.get('genre', 'general')
        
        # Send typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Send initial message
        status_msg = await update.message.reply_text(f"📖 Writing story about *{title}*... (AI is working)", parse_mode="Markdown")
        
        # Generate story
        story = await StoryGenerator.generate_story(title, genre)
        
        # Edit the status message with the story
        await status_msg.edit_text(story, parse_mode="Markdown")

# ============ MAIN ============
async def main():
    print("🚀 Starting Story Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot = StoryBot()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(CommandHandler("genre", bot.set_genre))
    application.add_handler(CommandHandler("status", bot.status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("📡 Starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Story Bot is LIVE!")
    print("📖 Ready to generate stories!")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    print("🌟 STORY BOT DEPLOYING...")
    asyncio.run(main())
