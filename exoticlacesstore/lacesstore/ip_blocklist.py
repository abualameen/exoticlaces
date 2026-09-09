# lacesstore/ip_blocklist.py
import re
import requests
from django.core.cache import cache

# Known bad IPs (blocked permanently)
PERMANENT_BLOCKLIST = [
    # Add IPs here if you keep getting bots from the same IPs
    # e.g., '123.45.67.89',
]

# IP ranges that are commonly bots
BLOCKED_IP_RANGES = [
    r'^52\.\d+\.\d+\.\d+',  # AWS (often bots)
    r'^54\.\d+\.\d+\.\d+',  # AWS
    r'^35\.\d+\.\d+\.\d+',  # Google Cloud
    r'^34\.\d+\.\d+\.\d+',  # Google Cloud
    r'^100\.\d+\.\d+\.\d+', # Cloudflare
    r'^104\.\d+\.\d+\.\d+', # Cloudflare
]

def is_ip_blocked(ip):
    """Check if an IP is permanently blocked"""
    if not ip:
        return False
    
    # Check permanent blocklist
    if ip in PERMANENT_BLOCKLIST:
        return True
    
    # Check IP ranges
    for pattern in BLOCKED_IP_RANGES:
        if re.search(pattern, ip):
            return True
    
    return False

def get_ip_reputation(ip):
    """Check IP reputation using a free API (optional)"""
    # You can use services like IPQualityScore, AbuseIPDB, etc.
    # For now, we'll just use the blocklist
    return is_ip_blocked(ip)