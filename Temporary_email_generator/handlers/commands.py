from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from database import (
    add_user, update_user_activity, get_active_email_account,
    save_email_account, get_user_email_accounts, get_user_email_count,
    deactivate_email_account, get_email_account_by_id,
    cache_message, get_cached_messages, mark_message_as_read
)
from mail_api import create_email_account, get_messages, read_message, delete_account
from keyboards.inline import get_main_keyboard, get_back_button
from config import MAX_EMAILS_PER_USER

router = Router()

# ============ CHANNEL PROMOTION CONFIGURATION ============
# 🔗 Replace with YOUR channel links
CHANNELS = [
    {"name": "Updates Channel", "url": "https://t.me/+aGM2VBSh_RI5OTU1"},
    {"name": "Support Group", "url": "https://t.me/+kXGi4enSKjc1MmM1"},
    {"name": "Community", "url": "https://t.me/smxopofficial"}
]

# Dictionary to track who saw promotion (in memory)
# Note: This resets when bot restarts - fine for testing
user_promotion_seen = {}


def get_channel_promotion_keyboard():
    """Create inline keyboard with channel links (Optional)"""
    keyboard = []

    # Add channel buttons
    for channel in CHANNELS:
        keyboard.append([InlineKeyboardButton(
            text=f"📢 Join {channel['name']}",
            url=channel['url']
        )])

    # Add continue button
    keyboard.append([
        InlineKeyboardButton(text="🚀 Continue to Bot", callback_data="continue_bot"),
        InlineKeyboardButton(text="ℹ️ Skip", callback_data="skip_promo")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ============ MODIFIED /start COMMAND (NO DATABASE CHANGES NEEDED) ============

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command with channel promotion"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Add user to database
    add_user(user_id, username, first_name, last_name)
    update_user_activity(user_id)

    # Check if user has already seen promotion (using memory dict)
    if user_id not in user_promotion_seen:
        # Mark as seen
        user_promotion_seen[user_id] = True

        # Send promotional message (NOT blocking)
        await message.answer(
            "<b>🌟 Welcome to Temp Mail Bot! 🌟</b>\n\n"
            "<b>📢 Support Us (Optional):</b>\n"
            "Join our channels for updates and tips!\n\n"
            "<i>✨ You can use the bot even if you don't join.</i>\n\n"
            "👇 <b>Click Continue to start:</b>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_channel_promotion_keyboard()
        )
        return

    # Regular start flow (user already saw promotion)
    existing_account = get_active_email_account(user_id)

    if existing_account:
        await message.answer(
            f"👋 Welcome back, {first_name}!\n\n"
            f"📧 Your active email: `{existing_account['email']}`\n\n"
            f"Use the buttons below to manage your temporary email:",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Create new email account
        await message.answer(
            f"👋 Welcome to Temp Mail Bot, {first_name}!\n\n"
            f"🔄 Creating your temporary email address..."
        )

        account = await create_email_account()

        if account:
            save_email_account(
                user_id,
                account['email'],
                account['password'],
                account['token'],
                account['domain']
            )

            await message.answer(
                f"✅ **Your temporary email is ready!**\n\n"
                f"📧 `{account['email']}`\n\n"
                f"🔒 This email will work for 30-60 minutes.\n"
                f"💡 Use /inbox to check messages or /new to create a new one.\n\n"
                f"What would you like to do?",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.answer(
                "❌ Failed to create email account. Please try again later.",
                reply_markup=get_back_button()
            )


# ============ CALLBACK HANDLER FOR PROMOTION BUTTONS ==========

@router.callback_query(F.data.in_(["continue_bot", "skip_promo"]))
async def handle_promotion_callback(callback: CallbackQuery):
    """Handle promotion button clicks"""
    user_id = callback.from_user.id

    # Edit the promotion message to show welcome
    await callback.message.edit_text(
        "✅ <b>Welcome to Temp Mail Bot!</b>\n\n"
        "You can now use all features.\n\n"
        "📧 Creating your temporary email...",
        parse_mode=ParseMode.HTML
    )

    # Create email account
    existing_account = get_active_email_account(user_id)

    if not existing_account:
        account = await create_email_account()

        if account:
            save_email_account(
                user_id,
                account['email'],
                account['password'],
                account['token'],
                account['domain']
            )

            await callback.message.edit_text(
                f"✅ **Your temporary email is ready!**\n\n"
                f"📧 `{account['email']}`\n\n"
                f"🔒 This email will work for 30-60 minutes.\n"
                f"💡 Use /inbox to check messages or /new to create a new one.\n\n"
                f"What would you like to do?",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await callback.message.edit_text(
                "❌ Failed to create email account. Please try again later.",
                reply_markup=get_back_button()
            )
    else:
        await callback.message.edit_text(
            f"✅ **Welcome back!**\n\n"
            f"📧 Your active email: `{existing_account['email']}`\n\n"
            f"Use the buttons below to manage your temporary email:",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    await callback.answer("Welcome to Temp Mail Bot! ✅")


# ============ REST OF YOUR EXISTING COMMANDS ============

@router.message(Command("new"))
async def cmd_new(message: Message):
    """Handle /new command - create new email"""
    user_id = message.from_user.id
    update_user_activity(user_id)

    email_count = get_user_email_count(user_id)

    if email_count >= MAX_EMAILS_PER_USER:
        await message.answer(
            f"⚠️ You have reached the maximum of {MAX_EMAILS_PER_USER} email accounts.\n"
            f"Please delete an existing account first using /delete"
        )
        return

    await message.answer("🔄 Creating a new temporary email address...")

    account = await create_email_account()

    if account:
        save_email_account(
            user_id,
            account['email'],
            account['password'],
            account['token'],
            account['domain']
        )

        await message.answer(
            f"✅ **New temporary email created!**\n\n"
            f"📧 `{account['email']}`\n\n"
            f"Use /inbox to check for messages.",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer("❌ Failed to create new email. Please try again.")


@router.message(Command("inbox"))
async def cmd_inbox(message: Message):
    """Handle /inbox command - show messages"""
    user_id = message.from_user.id
    update_user_activity(user_id)

    account = get_active_email_account(user_id)

    if not account:
        await message.answer(
            "⚠️ No active email account found. Please use /start to create one.",
            reply_markup=get_back_button()
        )
        return

    await message.answer("📬 Fetching your messages...")

    messages = await get_messages(account['token'])

    if not messages:
        await message.answer(
            "📭 Your inbox is empty.\n\n"
            f"📧 Your email: `{account['email']}`\n\n"
            f"Share this email to receive messages.",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    for msg in messages:
        cache_message(
            account['id'],
            msg['id'],
            msg.get('from', {}).get('address', 'Unknown'),
            msg.get('subject', ''),
            msg.get('text', ''),
            msg['createdAt']
        )

    cached_messages = get_cached_messages(account['id'], limit=10)

    if not cached_messages:
        await message.answer("📭 No messages found.")
        return

    response = f"📬 **Inbox for** `{account['email']}`\n\n"

    for idx, msg in enumerate(cached_messages[:5], 1):
        read_status = "✅" if msg['is_read'] else "🆕"
        response += f"{read_status} **{idx}.** From: `{msg['sender'][:30]}`\n"
        response += f"   📝 Subject: {msg['subject'][:50]}\n"
        response += f"   🕐 {msg['received_at'][:16]}\n\n"

    if len(cached_messages) > 5:
        response += f"_Showing 5 of {len(cached_messages)} messages. Use /read <number> to read._"

    await message.answer(response, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    """Handle /delete command - delete current email"""
    user_id = message.from_user.id
    update_user_activity(user_id)

    account = get_active_email_account(user_id)

    if not account:
        await message.answer("⚠️ No active email account to delete.")
        return

    success = await delete_account(account['token'])
    deactivate_email_account(account['id'])

    if success:
        await message.answer(
            f"✅ Email `{account['email']}` has been deleted.\n\n"
            f"Use /start to create a new one.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer(
            f"⚠️ Email `{account['email']}` has been deactivated locally.\n\n"
            f"Use /start to create a new one.",
            parse_mode=ParseMode.MARKDOWN
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
🤖 **Temp Mail Bot - Help**

**Commands:**
/start - Start the bot and create your first email
/new - Create a new temporary email address
/inbox - Check your inbox for messages
/delete - Delete your current email address
/help - Show this help message

**How to use:**
1. Use /start to get your temporary email address
2. Share that email address anywhere
3. Use /inbox to check for incoming messages
4. Use /delete when you're done

**Features:**
✅ Real temporary email addresses (via mail.tm)
✅ Instant email checking
✅ Multiple email accounts per user
✅ Messages cached locally

**⚠️ Note:** 
- Emails work for 30-60 minutes
- All data is private to your chat
- No personal information required

*For support or issues, contact @username*
"""
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)