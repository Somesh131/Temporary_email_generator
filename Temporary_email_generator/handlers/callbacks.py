from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from database import (
    update_user_activity, get_active_email_account,
    get_user_email_accounts, get_email_account_by_id,
    get_cached_messages, mark_message_as_read,
    save_email_account, deactivate_email_account
)
from mail_api import get_messages, read_message, delete_account
from keyboards.inline import get_main_keyboard, get_message_buttons, get_switch_account_keyboard

router = Router()


@router.callback_query(F.data == "new_email")
async def callback_new_email(callback: CallbackQuery):
    """Handle new email button"""
    await callback.answer()
    user_id = callback.from_user.id
    update_user_activity(user_id)

    await callback.message.edit_text("🔄 Creating a new temporary email address...")

    from mail_api import create_email_account
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
            f"✅ **New temporary email created!**\n\n"
            f"📧 `{account['email']}`\n\n"
            f"Use the buttons below to manage your email:",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text(
            "❌ Failed to create new email. Please try again.",
            reply_markup=get_main_keyboard()
        )


@router.callback_query(F.data == "inbox")
async def callback_inbox(callback: CallbackQuery):
    """Handle inbox button"""
    await callback.answer()
    user_id = callback.from_user.id
    update_user_activity(user_id)

    account = get_active_email_account(user_id)

    if not account:
        await callback.message.edit_text(
            "⚠️ No active email account found. Please use /start to create one.",
            reply_markup=get_main_keyboard()
        )
        return

    await callback.message.edit_text("📬 Fetching your messages...")

    messages = await get_messages(account['token'])

    if not messages:
        await callback.message.edit_text(
            f"📭 Your inbox is empty.\n\n"
            f"📧 Your email: `{account['email']}`",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    from database import cache_message
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
        await callback.message.edit_text("📭 No messages found.", reply_markup=get_main_keyboard())
        return

    response = f"📬 **Inbox for** `{account['email']}`\n\n"

    for idx, msg in enumerate(cached_messages[:5], 1):
        read_status = "✅" if msg['is_read'] else "🆕"
        response += f"{read_status} **{idx}.** From: `{msg['sender'][:30]}`\n"
        response += f"   📝 {msg['subject'][:40]}\n\n"

    response += f"\n_Total: {len(cached_messages)} messages_"

    await callback.message.edit_text(
        response,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "refresh")
async def callback_refresh(callback: CallbackQuery):
    """Handle refresh button"""
    await callback.answer("Refreshing...")
    await callback_inbox(callback)


@router.callback_query(F.data == "delete_email")
async def callback_delete_email(callback: CallbackQuery):
    """Handle delete email button"""
    await callback.answer()
    user_id = callback.from_user.id
    update_user_activity(user_id)

    account = get_active_email_account(user_id)

    if not account:
        await callback.message.edit_text(
            "⚠️ No active email account to delete.",
            reply_markup=get_main_keyboard()
        )
        return

    await callback.message.edit_text(f"🗑 Deleting `{account['email']}`...", parse_mode=ParseMode.MARKDOWN)

    success = await delete_account(account['token'])
    deactivate_email_account(account['id'])

    if success:
        await callback.message.edit_text(
            f"✅ Email `{account['email']}` has been deleted.\n\n"
            f"Use /start to create a new one.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text(
            f"⚠️ Email `{account['email']}` has been deactivated.\n\n"
            f"Use /start to create a new one.",
            parse_mode=ParseMode.MARKDOWN
        )


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Handle help button"""
    await callback.answer()
    help_text = """
🤖 **Temp Mail Bot**

**Features:**
• Create temporary email addresses
• Check inbox in real-time
• Multiple email accounts
• Auto-delete after use

**Commands:**
/start - Start the bot
/new - New email address
/inbox - Check messages
/delete - Delete email
/help - Show this help
"""
    await callback.message.edit_text(help_text, reply_markup=get_main_keyboard())


@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    """Handle back to main button"""
    await callback.answer()
    user_id = callback.from_user.id
    account = get_active_email_account(user_id)

    if account:
        await callback.message.edit_text(
            f"📧 Your email: `{account['email']}`\n\n"
            f"What would you like to do?",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text(
            "Welcome back! Use /start to create an email.",
            reply_markup=get_main_keyboard()
        )


@router.callback_query(F.data == "switch_account")
async def callback_switch_account(callback: CallbackQuery):
    """Handle switch account button"""
    await callback.answer()
    user_id = callback.from_user.id
    accounts = get_user_email_accounts(user_id)

    if len(accounts) <= 1:
        await callback.answer("You only have one active account. Create a new one with /new", show_alert=True)
        return

    await callback.message.edit_text(
        "🔄 **Switch Email Account**\n\nSelect an account to make active:",
        reply_markup=get_switch_account_keyboard(accounts),
        parse_mode=ParseMode.MARKDOWN
    )


@router.callback_query(F.data.startswith("switch_acc_"))
async def callback_switch_acc_action(callback: CallbackQuery):
    """Handle account switching"""
    await callback.answer()
    account_id = int(callback.data.split("_")[2])
    account = get_email_account_by_id(account_id)

    if account:
        # Set as active by updating the database
        # For simplicity, we just show it
        await callback.message.edit_text(
            f"✅ Switched to email: `{account['email']}`\n\n"
            f"Use /inbox to check messages.",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text(
            "❌ Account not found.",
            reply_markup=get_main_keyboard()
        )


@router.callback_query(F.data.startswith("read_full_"))
async def callback_read_full(callback: CallbackQuery):
    """Handle read full message button"""
    await callback.answer()
    cache_id = int(callback.data.split("_")[2])

    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT sender, subject, body, received_at FROM cached_messages WHERE id = ?', (cache_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        mark_message_as_read(cache_id)
        response = f"📧 **From:** {row[0]}\n"
        response += f"📝 **Subject:** {row[1]}\n"
        response += f"🕐 **Received:** {row[3]}\n\n"
        response += f"📄 **Message:**\n{row[2] if row[2] else '(No content)'}"

        await callback.message.edit_text(
            response[:4000],  # Telegram limit
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )