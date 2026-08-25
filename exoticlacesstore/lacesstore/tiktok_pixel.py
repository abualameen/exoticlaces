# lacesstore/tiktok_pixel.py
import json
import uuid
import hashlib
import hmac
import base64
import time
from django.conf import settings
from django.utils import timezone
import requests

class TikTokPixel:
    """TikTok Pixel Event Tracking"""
    
    def __init__(self):
        self.pixel_id = getattr(settings, 'TIKTOK_PIXEL_ID', '')
        self.enabled = getattr(settings, 'TIKTOK_PIXEL_ENABLED', False)
        self.access_token = getattr(settings, 'TIKTOK_ACCESS_TOKEN', '')
        self.test_event_code = getattr(settings, 'TIKTOK_TEST_EVENT_CODE', '')
        
        # ✅ Updated API endpoint
        self.api_base = "https://business-api.tiktok.com/open_api/v1.3/event/track/"
        
        if not self.pixel_id:
            print("⚠️ TikTok Pixel: TIKTOK_PIXEL_ID not configured in settings")
        else:
            print(f"✅ TikTok Pixel configured: {self.pixel_id}")
    
    def track_event(self, request, event_name, event_data=None, user_data=None):
        """Track a TikTok Pixel event"""
        if not self.enabled or not self.pixel_id:
            return
        
        # Get user data
        email = None
        phone = None
        if request and request.user.is_authenticated:
            email = request.user.email
            if hasattr(request.user, 'customer') and request.user.customer.phonenumber:
                phone = request.user.customer.phonenumber
        
        # ✅ Build the payload properly for TikTok Events API
        payload = {
            "pixel_id": self.pixel_id,
            "events": [{
                "event_id": str(uuid.uuid4()),
                "event_source": "web",
                "event_time": int(timezone.now().timestamp()),
                "event_name": event_name,
                "user_data": {
                    "em": [hashlib.sha256(email.lower().encode()).hexdigest()] if email else [],
                    "ph": [hashlib.sha256(phone.lower().encode()).hexdigest()] if phone else [],
                    "client_ip_address": self._get_client_ip(request) if request else '',
                    "client_user_agent": request.META.get('HTTP_USER_AGENT', '') if request else '',
                },
                "event_data": event_data or {},
            }]
        }
        
        # ✅ Add test event code if provided
        if self.test_event_code:
            payload["test_event_code"] = self.test_event_code
        
        # Send event via API
        self._send_event(payload)
    
    def _send_event(self, payload):
        """Send event to TikTok Business API"""
        if not self.access_token:
            print("⚠️ TikTok Pixel: No access token, skipping server-side event")
            return
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Access-Token": self.access_token,
            }
            
            response = requests.post(self.api_base, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    print(f"✅ TikTok Pixel event sent successfully")
                else:
                    print(f"❌ TikTok Pixel API error: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ TikTok Pixel HTTP error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ TikTok Pixel exception: {e}")
    
    def _hash(self, value):
        """Hash user data for TikTok (SHA-256)"""
        import hashlib
        if not value:
            return ""
        return hashlib.sha256(value.lower().strip().encode()).hexdigest()
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        if not request:
            return ""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# ✅ Lazy initialization
_tiktok_pixel = None

def get_tiktok_pixel():
    """Lazy initialization of TikTok Pixel"""
    global _tiktok_pixel
    if _tiktok_pixel is None:
        try:
            _tiktok_pixel = TikTokPixel()
        except Exception as e:
            print(f"⚠️ TikTok Pixel initialization error: {e}")
            _tiktok_pixel = None
    return _tiktok_pixel

def track_tiktok_event(request, event_name, event_data=None, user_data=None):
    """Helper function to track TikTok events"""
    pixel = get_tiktok_pixel()
    if pixel:
        pixel.track_event(request, event_name, event_data, user_data)