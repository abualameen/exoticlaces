# lacesstore/tiktok_pixel.py
import json
import uuid
from django.conf import settings
from django.utils import timezone
import requests

class TikTokPixel:
    """TikTok Pixel Event Tracking"""
    
    def __init__(self):
        # ✅ Use getattr with fallback to handle missing settings gracefully
        self.pixel_id = getattr(settings, 'TIKTOK_PIXEL_ID', '')
        self.enabled = getattr(settings, 'TIKTOK_PIXEL_ENABLED', False)
        self.access_token = getattr(settings, 'TIKTOK_ACCESS_TOKEN', '')
        self.test_event_code = getattr(settings, 'TIKTOK_TEST_EVENT_CODE', '')
        self.api_base = "https://business-api.tiktok.com/open_api/v1.3/pixel/event"
        
        # ✅ Log if pixel is not configured
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
        
        # Prepare event data
        event = {
            "event_id": str(uuid.uuid4()),
            "event_source": "web",
            "event_time": int(timezone.now().timestamp()),
            "event_name": event_name,
            "user_data": {
                "em": [self._hash(email)] if email else [],
                "ph": [self._hash(phone)] if phone else [],
                "client_ip_address": self._get_client_ip(request) if request else '',
                "client_user_agent": request.META.get('HTTP_USER_AGENT', '') if request else '',
            },
            "event_data": event_data or {},
        }
        
        # Send event via API (Server-side tracking)
        self._send_event(event)
    
    def _send_event(self, event):
        """Send event to TikTok Business API (Server-side)"""
        if not self.access_token:
            print(f"⚠️ TikTok Pixel: No access token, skipping server-side event: {event['event_name']}")
            return
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Access-Token": self.access_token,
            }
            payload = {
                "pixel_id": self.pixel_id,
                "events": [event],
                "test_event_code": self.test_event_code,
            }
            response = requests.post(self.api_base, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"✅ TikTok Pixel event sent: {event['event_name']}")
            else:
                print(f"❌ TikTok Pixel error: {response.text}")
        except Exception as e:
            print(f"❌ TikTok Pixel exception: {e}")
    
    def _hash(self, value):
        """Hash user data for TikTok"""
        import hashlib
        if not value:
            return ""
        return hashlib.md5(value.lower().strip().encode()).hexdigest()
    
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

# ✅ Only create instance if settings are available
def get_tiktok_pixel():
    """Lazy initialization of TikTok Pixel"""
    try:
        return TikTokPixel()
    except Exception as e:
        print(f"⚠️ TikTok Pixel initialization error: {e}")
        return None

# ✅ Use lazy initialization
_tiktok_pixel = None

def track_tiktok_event(request, event_name, event_data=None, user_data=None):
    """Helper function to track TikTok events"""
    global _tiktok_pixel
    if _tiktok_pixel is None:
        _tiktok_pixel = get_tiktok_pixel()
    
    if _tiktok_pixel:
        _tiktok_pixel.track_event(request, event_name, event_data, user_data)