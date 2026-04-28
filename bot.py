import asyncio
import os
import re
import random
from datetime import datetime, timedelta
from typing import Dict
from openai import AsyncOpenAI

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    exit(1)

print(f"✅ Story Bot starting...")
print(f"✅ OpenAI: {'Connected' if OPENAI_API_KEY else 'Not configured (using templates)'}")

# Initialize OpenAI client if API key provided
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Store campaigns
active_stories: Dict[int, Dict] = {}

# ============ AI STORY GENERATOR ============
class AIStoryGenerator:
    
    @staticmethod
    async def generate_with_ai(topic: str, part_number: int, total_parts: int, is_short: bool = False) -> str:
        """Generate a story using OpenAI API"""
        
        if not openai_client:
            # Fallback to template generator
            return AIStoryGenerator.generate_template_story(topic, part_number, total_parts, is_short)
        
        try:
            if is_short:
                prompt = f"""Write a short, engaging story (200-300 words) about: {topic}

The story should be:
- Captivating and emotional
- Have a clear beginning, middle, and end
- Include a meaningful lesson or message
- Suitable for a Telegram channel

Format: Use emojis, line breaks, and hashtags at the end."""
            else:
                if part_number == 1:
                    prompt = f"""Write Part 1 of a {total_parts}-part story series about: {topic}

Part 1 should:
- Introduce the main characters and setting
- Create intrigue and hook the reader
- End with a cliffhanger or "To be continued..."

Format: Include "Part 1/{total_parts}" in title. Use emojis and line breaks."""
                elif part_number == total_parts:
                    prompt = f"""Write the FINAL Part {part_number} of a {total_parts}-part story series about: {topic}

This part should:
- Resolve all conflicts and mysteries
- Provide a satisfying conclusion
- End with "THE END"

Format: Include "Part {part_number}/{total_parts} (Finale)" in title."""
                else:
                    prompt = f"""Write Part {part_number} of a {total_parts}-part story series about: {topic}

This part should:
- Advance the plot and develop characters
- Introduce new challenges or revelations
- End with a cliffhanger leading to Part {part_number + 1}

Format: Include "Part {part_number}/{total_parts}" in title."""
            
            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional storyteller. Write engaging, emotional stories for Telegram channels."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=600
            )
            
            story = response.choices[0].message.content
            story += f"\n\n#{topic.replace(' ', '')} #StoryTime"
            if not is_short and total_parts > 1:
                story += f" #Part{part_number}"
            
            return {'text': story, 'is_complete': part_number == total_parts}
            
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            # Fallback to template
            return AIStoryGenerator.generate_template_story(topic, part_number, total_parts, is_short)
    
    @staticmethod
    def generate_template_story(topic: str, part_number: int, total_parts: int, is_short: bool = False) -> dict:
        """Fallback template-based story generator"""
        
        openings = [
            "Once upon a time in a small town...",
            "In a world not so different from ours...",
            "It was a dark and stormy night when...",
            "The day started like any other, but then...",
        ]
        
        middles = [
            "suddenly, everything changed. A mysterious stranger appeared.",
            "something extraordinary occurred that would alter their lives forever.",
            "they discovered a hidden truth that had been buried for years.",
        ]
        
        endings = [
            "And from that day forward, nothing was ever the same again.",
            "They learned that sometimes the greatest adventures find you.",
            "The experience changed them, making them stronger and wiser.",
        ]
        
        if is_short or total_parts == 1:
            story = f"📖 *{topic.upper()}* 📖\n\n"
            story += f"{random.choice(openings)}\n\n"
            story += f"This is a story about {topic}. {random.choice(middles)}\n\n"
            story += f"{random.choice(endings)}\n\n✨ *The End* ✨"
        elif part_number == 1:
            story = f"📖 *{topic.upper()} - Part {part_number}/{total_parts}* 📖\n\n"
            story += f"{random.choice(openings)}\n\n"
            story += f"Our story begins...\n\n🔜 *To be continued...*"
        elif part_number == total_parts:
            story = f"📖 *{topic.upper()} - Part {part_number}/{total_parts} (Finale)* 📖\n\n"
            story += f"The thrilling conclusion!\n\n{random.choice(endings)}\n\n✨ *THE END* ✨"
        else:
            story = f"📖 *{topic.upper()} - Part {part_number}/{total_parts}* 📖\n\n"
            story += f"The story continues...\n\n{random.choice(middles)}\n\n🔜 *To be continued in Part {part_number + 1}...*"
        
        story += f"\n\n#{topic.replace(' ', '')} #StoryTime"
        if total_parts > 1:
            story += f" #Part{part_number}"
        
        return {'text': story, 'is_complete': part_number == total_parts}

# ============ BOT CLASS ============
class StoryBot:
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ai_status = "🤖 *AI POWERED*" if OPENAI_API_KEY else "📝 *Template Mode*"
        
        await update.message.reply_text(
            f"📖 *STORY TIME BOT* 📖\n\n"
            f"{ai_status}\n\n"
            f"*Commands:*\n"
            f"`/story @channel | topic | parts` - Start a story series\n"
            f"`/short @channel | topic` - One complete story\n"
            f"`/status` - Check progress\n"
            f"`/stop` - Stop story\n\n"
            f"*Examples:*\n"
            f"`/story @modernlovetips | A Lost Love | 5`\n"
            f"`/short @modernlovetips | A Kind Stranger`\n\n"
            f"✨ *AI creates unique, engaging stories!* ✨",
            parse_mode="Markdown"
        )
    
    async def start_story_series(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        match = re.search(r'/story\s+(@\S+)\s*\|\s*(.+?)\s*\|\s*(\d+)', text)
        
        if not match:
            await update.message.reply_text(
                "❌ Use: `/story @channel | topic | number_of_parts`\n"
                "Example: `/story @modernlovetips | A Lost Love | 5`"
            )
            return
        
        channel = match.group(1)
        topic = match.group(2)
        total_parts = int(match.group(3))
        
        if total_parts < 2 or total_parts > 30:
            await update.message.reply_text("❌ Parts must be between 2 and 30")
            return
        
        # Stop existing story if any
        if user_id in active_stories:
            del active_stories[user_id]
        
        # Create new story campaign
        active_stories[user_id] = {
            'channel': channel,
            'topic': topic,
            'total_parts': total_parts,
            'current_part': 0,
            'posts_made': 0,
            'start_date': datetime.now(),
            'is_series': True
        }
        
        ai_text = "🤖 OpenAI will generate each part uniquely!" if OPENAI_API_KEY else "📝 Using premium templates"
        
        await update.message.reply_text(
            f"📖 *STORY SERIES STARTED!* 📖\n\n"
            f"📢 Channel: {channel}\n"
            f"📝 Topic: {topic}\n"
            f"📚 Total Parts: {total_parts}\n"
            f"⏱️ Posting: Every 3 hours\n"
            f"{ai_text}\n\n"
            f"✨ Part 1 arriving soon...\n"
            f"Use /status to track progress",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(2)
        await self.post_next_story_part(update, context)
    
    async def start_short_story(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        
        match = re.search(r'/short\s+(@\S+)\s*\|\s*(.+?)$', text)
        
        if not match:
            await update.message.reply_text(
                "❌ Use: `/short @channel | topic`\n"
                "Example: `/short @modernlovetips | A Kind Stranger`"
            )
            return
        
        channel = match.group(1)
        topic = match.group(2)
        
        await update.message.reply_text(f"📖 Generating your story about '{topic}'... (AI is working)")
        
        story = await AIStoryGenerator.generate_with_ai(topic, 1, 1, is_short=True)
        
        try:
            await context.bot.send_message(
                chat_id=channel,
                text=story['text'],
                parse_mode="Markdown"
            )
            await update.message.reply_text(f"✅ Short story posted to {channel}!")
            print(f"✅ Short story posted to {channel} - Topic: {topic}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}\nMake sure I'm admin in {channel}")
    
    async def post_next_story_part(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in active_stories:
            return
        
        story = active_stories[user_id]
        
        if story['current_part'] >= story['total_parts']:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ *Story Complete!*\n\nTopic: {story['topic']}\nTotal parts: {story['total_parts']}\n\nStart a new story with /story",
                parse_mode="Markdown"
            )
            del active_stories[user_id]
            return
        
        story['current_part'] += 1
        story['posts_made'] += 1
        
        # Generate part with AI
        part = await AIStoryGenerator.generate_with_ai(
            story['topic'], 
            story['current_part'], 
            story['total_parts'],
            is_short=False
        )
        
        try:
            await context.bot.send_message(
                chat_id=story['channel'],
                text=part['text'],
                parse_mode="Markdown"
            )
            print(f"✅ Part {story['current_part']}/{story['total_parts']} to {story['channel']}")
            
            if not part['is_complete']:
                asyncio.create_task(self.schedule_next_part(update, context, 10800))  # 3 hours
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 *Story Complete!* 🎉\n\n'{story['topic']}' has finished!\nTotal parts: {story['total_parts']}",
                    parse_mode="Markdown"
                )
                del active_stories[user_id]
                
        except Exception as e:
            print(f"❌ Error posting: {e}")
    
    async def schedule_next_part(self, update: Update, context: ContextTypes.DEFAULT_TYPE, delay_seconds: int):
        await asyncio.sleep(delay_seconds)
        await self.post_next_story_part(update, context)
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in active_stories:
            await update.message.reply_text("❌ No active story series. Start one with `/story`")
            return
        
        story = active_stories[user_id]
        remaining = story['total_parts'] - story['current_part']
        ai_status = "🤖 AI-generated" if OPENAI_API_KEY else "📝 Template mode"
        
        await update.message.reply_text(
            f"📊 *Story Status*\n\n"
            f"📢 Channel: {story['channel']}\n"
            f"📝 Topic: {story['topic']}\n"
            f"🎨 Mode: {ai_status}\n"
            f"📚 Progress: Part {story['current_part']} of {story['total_parts']}\n"
            f"📨 Total parts: {story['posts_made']}\n"
            f"⏰ Remaining: {remaining} parts\n"
            f"🔄 Next part in: ~3 hours\n\n"
            f"Use /stop to end this story",
            parse_mode="Markdown"
        )
    
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id in active_stories:
            story = active_stories[user_id]
            parts_posted = story['current_part']
            del active_stories[user_id]
            
            await update.message.reply_text(
                f"🛑 *Story Stopped*\n\n"
                f"Topic: {story['topic']}\n"
                f"Parts posted: {parts_posted} of {story['total_parts']}\n\n"
                f"Start a new story with /story",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ No active story to stop")

# ============ MAIN ============
async def main():
    print("🚀 Starting AI Story Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot = StoryBot()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("story", bot.start_story_series))
    application.add_handler(CommandHandler("short", bot.start_short_story))
    application.add_handler(CommandHandler("status", bot.status))
    application.add_handler(CommandHandler("stop", bot.stop))
    
    print("📡 Starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ AI Story Bot is LIVE!")
    print(f"📖 OpenAI: {'Connected - AI stories enabled!' if OPENAI_API_KEY else 'Not connected - using templates'}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    print("🌟 AI STORY BOT DEPLOYING...")
    asyncio.run(main())
