import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import commands, callbacks

# Create bot instance GLOBALLY
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


async def main():
    """Main entry point for the bot"""

    # Initialize database
    init_db()
    logging.info("Database initialized")

    dp = Dispatcher()

    # Include routers
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)

    # Start polling
    logging.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")