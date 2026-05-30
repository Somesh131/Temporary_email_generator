import re
import random
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from email.utils import parsedate_to_datetime


# ==================== EMAIL VALIDATION HELPERS ====================

def is_valid_email(email: str) -> bool:
    """
    Validate email format using regex

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def extract_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address

    Args:
        email: Email address

    Returns:
        Domain part of email or None if invalid
    """
    if is_valid_email(email):
        return email.split('@')[1]
    return None


def extract_username(email: str) -> Optional[str]:
    """
    Extract username from email address

    Args:
        email: Email address

    Returns:
        Username part of email or None if invalid
    """
    if is_valid_email(email):
        return email.split('@')[0]
    return None


# ==================== STRING GENERATION HELPERS ====================

def generate_random_string(length: int = 10, include_digits: bool = True,
                           include_special: bool = False) -> str:
    """
    Generate random string of specified length

    Args:
        length: Length of string to generate
        include_digits: Whether to include digits
        include_special: Whether to include special characters

    Returns:
        Random generated string
    """
    chars = string.ascii_lowercase
    if include_digits:
        chars += string.digits
    if include_special:
        chars += "!@#$%^&*"

    return ''.join(random.choices(chars, k=length))


def generate_username(style: str = "random", length: int = 12) -> str:
    """
    Generate random username with different styles

    Args:
        style: Style of username ('random', 'wordlike', 'timestamp')
        length: Length for random style

    Returns:
        Generated username
    """
    if style == "timestamp":
        return f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"
    elif style == "wordlike":
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        username = ''
        for i in range(length // 2):
            username += random.choice(consonants) + random.choice(vowels)
        return username[:length]
    else:  # random
        return generate_random_string(length, include_digits=True, include_special=False)


# ==================== DATE & TIME HELPERS ====================

def format_timestamp(timestamp: str, format_type: str = "relative") -> str:
    """
    Format timestamp for display

    Args:
        timestamp: ISO format timestamp string
        format_type: 'relative' (e.g., "2 minutes ago") or 'absolute' (e.g., "14:30")

    Returns:
        Formatted timestamp string
    """
    try:
        # Parse ISO timestamp
        if 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        if format_type == "relative":
            return get_relative_time(dt)
        else:
            return dt.strftime("%H:%M:%S")
    except Exception:
        return timestamp


def get_relative_time(dt: datetime) -> str:
    """
    Convert datetime to relative time string (e.g., "5 minutes ago")

    Args:
        dt: datetime object

    Returns:
        Relative time string
    """
    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 7:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def is_email_expired(created_at: str, max_age_minutes: int = 60) -> bool:
    """
    Check if email account has expired

    Args:
        created_at: Creation timestamp string
        max_age_minutes: Maximum age in minutes

    Returns:
        True if expired, False otherwise
    """
    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now()
        age_minutes = (now - created).total_seconds() / 60
        return age_minutes > max_age_minutes
    except Exception:
        return False


# ==================== TEXT FORMATTING HELPERS ====================

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: String to append when truncated

    Returns:
        Truncated text
    """
    if not text:
        return "(No content)"

    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text

    Args:
        text: Text that might contain HTML

    Returns:
        Clean text without HTML
    """
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Replace common HTML entities
    html_entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
    }
    for entity, replacement in html_entities.items():
        clean = clean.replace(entity, replacement)
    return clean.strip()


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for Markdown
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_email_preview(sender: str, subject: str, body: str, max_length: int = 100) -> str:
    """
    Format email preview for inbox display

    Args:
        sender: Sender email address
        subject: Email subject
        body: Email body
        max_length: Maximum preview length

    Returns:
        Formatted preview string
    """
    preview = f"📧 From: {truncate_text(sender, 30)}\n"
    preview += f"📝 Subject: {truncate_text(subject, 40)}\n"
    preview += f"📄 Preview: {truncate_text(clean_html(body), max_length)}"
    return preview


def format_message_for_display(sender: str, subject: str, body: str, received_at: str) -> str:
    """
    Format full message for display

    Args:
        sender: Sender email address
        subject: Email subject
        body: Email body
        received_at: Received timestamp

    Returns:
        Formatted message string
    """
    formatted_time = format_timestamp(received_at, "absolute")
    relative_time = format_timestamp(received_at, "relative")

    message = f"📧 **From:** {escape_markdown(sender)}\n"
    message += f"📝 **Subject:** {escape_markdown(subject)}\n"
    message += f"🕐 **Received:** {formatted_time} ({relative_time})\n\n"
    message += f"📄 **Message:**\n{escape_markdown(clean_html(body))}"

    return message


# ==================== VALIDATION HELPERS ====================

def validate_input_length(text: str, max_length: int = 1000) -> bool:
    """
    Validate input length

    Args:
        text: Input text to validate
        max_length: Maximum allowed length

    Returns:
        True if valid, False otherwise
    """
    return len(text) <= max_length


def sanitize_input(text: str) -> str:
    """
    Sanitize user input

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Trim whitespace
    text = text.strip()
    # Limit length
    text = text[:1000]
    return text


# ==================== MESSAGE PARSING HELPERS ====================

def extract_links(text: str) -> List[str]:
    """
    Extract URLs from text

    Args:
        text: Text to extract links from

    Returns:
        List of URLs found
    """
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
    return re.findall(url_pattern, text)


def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract email addresses from text

    Args:
        text: Text to extract emails from

    Returns:
        List of email addresses found
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)


# ==================== BOT-RESPONSE HELPERS ====================

def get_random_greeting() -> str:
    """
    Get random greeting message

    Returns:
        Random greeting string
    """
    greetings = [
        "👋 Hey there!",
        "🎉 Welcome aboard!",
        "🚀 Ready for temp emails?",
        "📧 Your temporary inbox awaits!",
        "✨ Magic email incoming!",
        "💫 Poof! Your temp email is ready!",
        "🌟 Welcome to the temp email club!",
        "🎯 Let's get you a temporary email!"
    ]
    return random.choice(greetings)


def get_random_tip() -> str:
    """
    Get random usage tip

    Returns:
        Random tip string
    """
    tips = [
        "💡 Tip: You can have up to 5 active email accounts!",
        "💡 Tip: Emails automatically expire after 60 minutes",
        "💡 Tip: Use /delete to remove your email when done",
        "💡 Tip: Your inbox updates in real-time!",
        "💡 Tip: Share your temp email anywhere - it's anonymous!",
        "💡 Tip: Use /new to create multiple email addresses",
        "💡 Tip: All messages are private to your chat"
    ]
    return random.choice(tips)


def get_error_message(error_type: str) -> str:
    """
    Get user-friendly error message

    Args:
        error_type: Type of error ('api', 'network', 'rate_limit', 'general')

    Returns:
        User-friendly error message
    """
    errors = {
        'api': "❌ Sorry, the email service is temporarily unavailable. Please try again later.",
        'network': "🌐 Network error detected. Please check your connection and try again.",
        'rate_limit': "⏳ You're creating emails too quickly! Please wait a moment.",
        'general': "❌ Something went wrong. Please try again in a few moments.",
        'no_account': "⚠️ No active email account found. Use /start to create one.",
        'inbox_empty': "📭 Your inbox is empty. Share your email to receive messages!",
        'invalid_command': "❓ Command not recognized. Use /help to see available commands."
    }
    return errors.get(error_type, errors['general'])


# ==================== STATISTICS & FORMATTING HELPERS ====================

def format_size(size_bytes: int) -> str:
    """
    Format bytes to human-readable size

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_number(num: int) -> str:
    """
    Format number with K/M/B suffix

    Args:
        num: Number to format

    Returns:
        Formatted number string
    """
    if num < 1000:
        return str(num)
    elif num < 1_000_000:
        return f"{num / 1000:.1f}K"
    elif num < 1_000_000_000:
        return f"{num / 1_000_000:.1f}M"
    else:
        return f"{num / 1_000_000_000:.1f}B"


# ==================== PROGRESS & STATUS HELPERS ====================

def create_progress_bar(percentage: float, length: int = 10,
                        filled_char: str = "█", empty_char: str = "░") -> str:
    """
    Create a text-based progress bar

    Args:
        percentage: Progress percentage (0-100)
        length: Length of progress bar in characters
        filled_char: Character for filled portion
        empty_char: Character for empty portion

    Returns:
        Progress bar string
    """
    filled_length = int(length * percentage // 100)
    return filled_char * filled_length + empty_char * (length - filled_length)


def get_status_emoji(status: str) -> str:
    """
    Get emoji for different status types

    Args:
        status: Status type ('active', 'expired', 'success', 'error', 'warning', 'info')

    Returns:
        Corresponding emoji
    """
    emojis = {
        'active': "🟢",
        'inactive': "⚫",
        'expired': "🔴",
        'success': "✅",
        'error': "❌",
        'warning': "⚠️",
        'info': "ℹ️",
        'email': "📧",
        'inbox': "📬",
        'trash': "🗑",
        'refresh': "🔄",
        'new': "🆕",
        'read': "📖",
        'unread': "🆕"
    }
    return emojis.get(status, "📌")


# ==================== CACHE & MEMORY HELPERS ====================

class SimpleCache:
    """
    Simple in-memory cache with TTL (Time To Live)
    """

    def __init__(self, default_ttl_seconds: int = 300):
        self.cache = {}
        self.default_ttl = default_ttl_seconds

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses default if None)
        """
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        if key in self.cache:
            if datetime.now() < self.cache[key]['expires_at']:
                return self.cache[key]['value']
            else:
                del self.cache[key]
        return None

    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """Clear all cache"""
        self.cache.clear()

    def cleanup(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, data in self.cache.items()
            if now >= data['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]


# ==================== RATE LIMITING HELPERS ====================

class RateLimiter:
    """
    Simple rate limiter for user actions
    """

    def __init__(self, max_requests: int = 10, time_window_seconds: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window_seconds
        self.requests = {}

    def is_allowed(self, user_id: int) -> bool:
        """
        Check if user is allowed to perform action

        Args:
            user_id: User ID

        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if (now - req_time).total_seconds() < self.time_window
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Add current request
        self.requests[user_id].append(now)
        return True

    def get_remaining(self, user_id: int) -> int:
        """Get remaining requests allowed for user"""
        if user_id not in self.requests:
            return self.max_requests

        now = datetime.now()
        recent_requests = [
            req_time for req_time in self.requests[user_id]
            if (now - req_time).total_seconds() < self.time_window
        ]

        return max(0, self.max_requests - len(recent_requests))


# ==================== BATCH PROCESSING HELPERS ====================

def chunk_list(items: List, chunk_size: int) -> List[List]:
    """
    Split a list into smaller chunks

    Args:
        items: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def batch_process(items: List, callback, batch_size: int = 10) -> List:
    """
    Process a list in batches

    Args:
        items: List of items to process
        callback: Function to process each batch
        batch_size: Size of each batch

    Returns:
        Combined results from all batches
    """
    results = []
    chunks = chunk_list(items, batch_size)

    for chunk in chunks:
        batch_result = callback(chunk)
        if batch_result:
            results.extend(batch_result)

    return results