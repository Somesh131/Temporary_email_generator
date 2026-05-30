import aiohttp
import random
import string
from typing import Optional, Dict, List, Any

from config import (
    MAIL_API_BASE,
    MAIL_DOMAINS_ENDPOINT,
    MAIL_ACCOUNTS_ENDPOINT,
    MAIL_MESSAGES_ENDPOINT
)


async def get_available_domains() -> List[str]:
    """Get list of available email domains"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(MAIL_DOMAINS_ENDPOINT) as response:
                if response.status == 200:
                    data = await response.json()
                    return [domain['domain'] for domain in data.get('hydra:member', [])]
        except Exception as e:
            print(f"Error fetching domains: {e}")
    return ["mail.tm"]


async def generate_random_username(length: int = 12) -> str:
    """Generate random username for email"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


async def create_email_account(domain: str = None) -> Optional[Dict]:
    """Create a new temporary email account"""
    if not domain:
        domains = await get_available_domains()
        domain = domains[0] if domains else "mail.tm"

    username = await generate_random_username()
    email = f"{username}@{domain}"
    password = await generate_random_username(16)

    async with aiohttp.ClientSession() as session:
        try:
            # Create account
            async with session.post(MAIL_ACCOUNTS_ENDPOINT, json={
                "address": email,
                "password": password
            }) as response:
                if response.status == 201:
                    account_data = await response.json()

                    # Get token
                    async with session.post(f"{MAIL_API_BASE}/token", json={
                        "address": email,
                        "password": password
                    }) as token_response:
                        if token_response.status == 200:
                            token_data = await token_response.json()
                            return {
                                "email": email,
                                "password": password,
                                "token": token_data.get('token'),
                                "domain": domain,
                                "id": account_data.get('id')
                            }
        except Exception as e:
            print(f"Error creating account: {e}")
    return None


async def get_messages(token: str) -> List[Dict]:
    """Get all messages for an email account"""
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(MAIL_MESSAGES_ENDPOINT, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('hydra:member', [])
        except Exception as e:
            print(f"Error fetching messages: {e}")
    return []


async def read_message(token: str, message_id: str) -> Optional[Dict]:
    """Read a specific message by ID"""
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{MAIL_MESSAGES_ENDPOINT}/{message_id}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error reading message: {e}")
    return None


async def delete_message(token: str, message_id: str) -> bool:
    """Delete a specific message"""
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(f"{MAIL_MESSAGES_ENDPOINT}/{message_id}", headers=headers) as response:
                return response.status == 204
        except Exception as e:
            print(f"Error deleting message: {e}")
    return False


async def delete_account(token: str) -> bool:
    """Delete the email account"""
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        try:
            # Get account ID first
            async with session.get(f"{MAIL_API_BASE}/me", headers=headers) as me_response:
                if me_response.status == 200:
                    me_data = await me_response.json()
                    account_id = me_data.get('id')

                    if account_id:
                        async with session.delete(f"{MAIL_ACCOUNTS_ENDPOINT}/{account_id}",
                                                  headers=headers) as delete_response:
                            return delete_response.status == 204
        except Exception as e:
            print(f"Error deleting account: {e}")
    return False