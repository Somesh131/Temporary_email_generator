from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📧 New Email", callback_data="new_email"),
            InlineKeyboardButton(text="📬 Inbox", callback_data="inbox")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh"),
            InlineKeyboardButton(text="❌ Delete Email", callback_data="delete_email")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Help", callback_data="help"),
            InlineKeyboardButton(text="🔄 Switch Account", callback_data="switch_account")
        ]
    ])

def get_message_buttons(message_id: str, message_cache_id: int) -> InlineKeyboardMarkup:
    """Buttons for a specific message"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📖 Read Full", callback_data=f"read_full_{message_cache_id}"),
            InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_msg_{message_id}")
        ],
        [InlineKeyboardButton(text="◀️ Back to Inbox", callback_data="inbox")]
    ])

def get_back_button() -> InlineKeyboardMarkup:
    """Simple back button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="back_to_main")]
    ])

def get_switch_account_keyboard(accounts: list) -> InlineKeyboardMarkup:
    """Keyboard for switching between email accounts"""
    keyboard = []
    for account in accounts[:5]:  # Max 5 accounts
        keyboard.append([InlineKeyboardButton(
            text=account['email'],
            callback_data=f"switch_acc_{account['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="◀️ Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)