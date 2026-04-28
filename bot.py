import asyncio
import os
import re
import random
from datetime import datetime, timedelta
from typing import Dict

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    exit(1)

print(f"✅ Story Bot starting...")

# Store campaigns
active_stories: Dict[int, Dict] = {}

# ============ STORY GENERATOR (No API needed) ============
class StoryGenerator:
    
    # Story openings
    OPENINGS = [
        "Once upon a time in a small town...",
        "In a world not so different from ours...",
        "It was a dark and stormy night when...",
        "The day started like any other, but then...",
        "Nobody expected what happened next when...",
        "Legend tells of a time when...",
        "In the heart of the city, where dreams are made...",
        "Far away, in a land of mystery...",
    ]
    
    # Story middles
    MIDDLES = [
        "suddenly, everything changed. A mysterious stranger appeared.",
        "something extraordinary occurred that would alter their lives forever.",
        "they discovered a hidden truth that had been buried for years.",
        "an unexpected twist turned their world upside down.",
        "fate intervened in ways nobody could have predicted.",
        "a secret was revealed that shocked everyone.",
        "the impossible became possible in the blink of an eye.",
        "courage was tested, and friendships were forged in fire.",
    ]
    
    # Story endings
    ENDINGS = [
        "And from that day forward, nothing was ever the same again.",
        "They learned that sometimes the greatest adventures find you.",
        "The experience changed them, making them stronger and wiser.",
        "And so, their journey continued, full of hope and wonder.",
        "It was a reminder that magic exists in everyday moments.",
        "They carried the lesson with them for the rest of their lives.",
        "The story became legend, passed down through generations.",
        "And they lived, not just happily, but meaningfully ever after.",
    ]
    
    @staticmethod
    def generate_story(topic: str, part_number: int, total_parts: int = 10) -> dict:
        """Generate a complete story or story part"""
        
        if total_parts == 1:
            # Complete short story
            opening = random.choice(StoryGenerator.OPENINGS)
            middle = random.choice(StoryGenerator.MIDDLES)
            ending = random.choice(StoryGenerator.ENDINGS)
            
            story = f"📖 *{topic.upper()}* 📖\n\n"
            story += f"{opening}\n\n"
            story += f"This is a story about {topic.lower()}. {middle}\n\n"
            story += f"{ending}\n\n"
            story += f"✨ *The End* ✨\n\n"
            story += f"#{topic.replace(' ', '')} #StoryTime"
            
            return {'text': story, 'is_complete': True}
        
        else:
            # Multi-part story (like a series)
            if part_number == 1:
                # Part 1: Introduction
                story = f"📖 *{topic.upper()} - Part {part_number}/{total_parts}* 📖\n\n"
                story += f"{random.choice(StoryGenerator.OPENINGS)}\n\n"
                story += f"Our story begins with {topic.lower()}...\n\n"
                story += f"The stage is set for an incredible journey. Little did anyone know what lay ahead...\n\n"
                story += f"🔜 *To be continued...*"
                
            elif part_number == total_parts:
                # Final part: Conclusion
                story = f"📖 *{topic.upper()} - Part {part_number}/{total_parts} (Finale)* 📖\n\n"
                story += f"The thrilling conclusion to our {topic.lower()} story!\n\n"
                story += f"{random.choice(StoryGenerator.ENDINGS)}\n\n"
                story += f"✨ *THE END* ✨\n\n"
                story += f"Thank you for following this story! 🙏"
                
            else:
                # Middle parts: Development
                story = f"📖 *{topic.upper()} - Part {part_number}/{total_parts}* 📖\n\n"
                story += f"The story continues...\n\n"
                story += f"{random.choice(StoryGenerator.MIDDLES)}\n\n"
                story += f"New challenges arise, characters grow, and the plot thickens...\n\n"
                story += f"🔜 *To be continued in Part {part_number + 1}...*"
            
            story += f"\n\n#{topic.replace(' ', '')} #StoryTime #Part{part_number}"
            
            return {'text': story, 'is_complete': part_number == total_parts}

# ============ BOT CLASS ============
class StoryBot:
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 *STORY TIME BOT* 📖\n\n"
            "I create engaging stories on ANY topic you give me!\n\n"
            "*Commands:*\n"
            "`/story @channel | topic | parts` - Start a story series\n"
            "`/short @channel | topic` - Post one complete story\n"
            "`/status` - Check story progress\n"
            "`/stop` - Stop story series\n\n"
            "*Examples:*\n"
            "`/story @modernlovetips | A Lost Love Returns | 5`\n"
            "`/short @modernlovetips | A Kind Stranger`\n\n"
            "The bot will post automatically every few hours!",
            parse_mode="Markdown"
        )
    
    async def start_story_series(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a multi-part story series"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Parse: /story @channel | topic | parts
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
        
        await update.message.reply_text(
            f"📖 *STORY SERIES STARTED!* 📖\n\n"
            f"📢 Channel: {channel}\n"
            f"📝 Topic: {topic}\n"
            f"📚 Total Parts: {total_parts}\n"
            f"⏱️ Posting: Every 3 hours\n\n"
            f"✨ Part 1 will arrive in a few seconds...\n"
            f"Use /status to track progress",
            parse_mode="Markdown"
        )
        
        # Send first part
        await asyncio.sleep(2)
        await self.post_next_story_part(update, context)
    
    async def start_short_story(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post a single complete story"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Parse: /short @channel | topic
        match = re.search(r'/short\s+(@\S+)\s*\|\s*(.+?)$', text)
        
        if not match:
            await update.message.reply_text(
                "❌ Use: `/short @channel | topic`\n"
                "Example: `/short @modernlovetips | A Kind Stranger`"
            )
            return
        
        channel = match.group(1)
        topic = match.group(2)
        
        # Generate and post story
        story = StoryGenerator.generate_story(topic, 1, 1)
        
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
        """Post the next part of the story series"""
        user_id = update.effective_user.id
        
        if user_id not in active_stories:
            return
        
        story = active_stories[user_id]
        
        # Check if story is complete
        if story['current_part'] >= story['total_parts']:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ *Story Complete!*\n\n"
                     f"Topic: {story['topic']}\n"
                     f"Total parts: {story['total_parts']}\n\n"
                     f"Start a new story with /story",
                parse_mode="Markdown"
            )
            del active_stories[user_id]
            return
        
        # Generate next part
        story['current_part'] += 1
        story['posts_made'] += 1
        
        part = StoryGenerator.generate_story(
            story['topic'], 
            story['current_part'], 
            story['total_parts']
        )
        
        # Post to channel
        try:
            await context.bot.send_message(
                chat_id=story['channel'],
                text=part['text'],
                parse_mode="Markdown"
            )
            print(f"✅ Posted Part {story['current_part']}/{story['total_parts']} to {story['channel']}")
            
            # Schedule next part if not complete
            if not part['is_complete']:
                # Schedule next part in 3 hours
                asyncio.create_task(self.schedule_next_part(update, context, 10800))  # 3 hours
            else:
                # Story complete
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 *Story Complete!* 🎉\n\n"
                         f"'{story['topic']}' has finished!\n"
                         f"Total parts: {story['total_parts']}\n\n"
                         f"Start a new story with /story",
                    parse_mode="Markdown"
                )
                del active_stories[user_id]
                
        except Exception as e:
            print(f"❌ Error posting story: {e}")
    
    async def schedule_next_part(self, update: Update, context: ContextTypes.DEFAULT_TYPE, delay_seconds: int):
        """Schedule the next story part"""
        await asyncio.sleep(delay_seconds)
        await self.post_next_story_part(update, context)
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in active_stories:
            await update.message.reply_text(
                "❌ No active story series.\n"
                "Start one with: `/story @channel | topic | parts`"
            )
            return
        
        story = active_stories[user_id]
        remaining = story['total_parts'] - story['current_part']
        
        await update.message.reply_text(
            f"📊 *Story Status*\n\n"
            f"📢 Channel: {story['channel']}\n"
            f"📝 Topic: {story['topic']}\n"
            f"📚 Progress: Part {story['current_part']} of {story['total_parts']}\n"
            f"📨 Posts made: {story['posts_made']}\n"
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
    print("🚀 Starting Story Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot = StoryBot()
    
    # Commands
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("story", bot.start_story_series))
    application.add_handler(CommandHandler("short", bot.start_short_story))
    application.add_handler(CommandHandler("status", bot.status))
    application.add_handler(CommandHandler("stop", bot.stop))
    
    print("📡 Starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Story Bot is LIVE!")
    print("📖 Ready to tell amazing stories!")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    print("🌟 STORY BOT DEPLOYING...")
    asyncio.run(main())
