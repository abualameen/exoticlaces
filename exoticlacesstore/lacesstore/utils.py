# lacesstore/utils.py
import re

DISPOSABLE_DOMAINS = [
    'tempmail.com', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'yopmail.com', 'throwawaymail.com',
    'trashmail.com', 'fakeinbox.com', 'getairmail.com',
    'spambox.us', 'mailcatch.com', 'mailexpire.com',
    'temp-mail.org', 'throwaway.email', 'mailnesia.com',
    'mintemail.com', 'spamgourmet.com', 'spamspot.com',
    'tempinbox.com', 'tmpmail.net', 'tempmail.net',
    'guerrillamail.net', 'guerrillamail.biz', 'guerrillamail.org',
    'guerrillamail.com', 'guerrillamail.de', 'guerrillamail.info',
    'guerrillamail.ws', 'guerrillamail.fr', 'guerrillamail.xyz',
    'mailinator.net', 'mailinator.org', 'mailinator.co',
    'mailinator.xyz', 'mailinator.info', 'mailinator.club',
    'mailinator.gq', 'mailinator.ml', 'mailinator.ga',
    'mailinator.cf', 'mailinator.tk', 'mailinator.top',
    '10minutemail.net', '10minutemail.co.uk', '10minutemail.com.au',
    '10minutemail.org', '10minutemail.info', '10minutemail.xyz',
    '10minutemail.tech', '10minutemail.site', '10minutemail.online',
    '10minutemail.club', '10minutemail.life', '10minutemail.work',
    '10minutemail.biz', '10minutemail.cloud', '10minutemail.design',
    '10minutemail.eu', '10minutemail.host', '10minutemail.io',
    '10minutemail.me', '10minutemail.network', '10minutemail.press',
    '10minutemail.shop', '10minutemail.store', '10minutemail.us',
]

def is_disposable_email(email):
    """Check if email is from a disposable domain"""
    if not email:
        return False
    domain = email.split('@')[-1].lower()
    return domain in DISPOSABLE_DOMAINS

def is_suspicious_username(username):
    """Check if username looks randomly generated"""
    if not username:
        return False
    
    # Check if username contains random patterns
    # Bots often use 8-12 random characters
    if len(username) >= 8 and username.islower() and all(c.isalpha() for c in username):
        # Check for common bot patterns
        vowels = set('aeiou')
        vowel_count = sum(1 for c in username if c in vowels)
        # Less than 20% vowels is suspicious
        if vowel_count / len(username) < 0.2:
            return True
    
    # Check for repeated patterns that bots use
    if re.search(r'(.)\1{3,}', username):  # 3+ repeated characters
        return True
    
    # Check for keyboard patterns (bots sometimes use keyboard smashes)
    keyboard_patterns = ['qwerty', 'asdf', 'zxcv', 'qwer', 'asdfg']
    for pattern in keyboard_patterns:
        if pattern in username.lower():
            return True
    
    return False