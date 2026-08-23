# lacesstore/tiktok_pixel.py
import json
import uuid
from django.conf import settings
from django.utils import timezone
import requests

class TikTokPixel:
    """TikTok Pixel Event Tracking"""
    
    def __init__(self):
        self.pixel_id = settings.TIKTOK_PIXEL_ID
        self.enabled = getattr(settings, 'TIKTOK_PIXEL_ENABLED', True)
        self.api_base = "https://business-api.tiktok.com/open_api/v1.3/pixel/event"
    
    def track_event(self, request, event_name, event_data=None, user_data=None):
        """Track a TikTok Pixel event"""
        if not self.enabled or not self.pixel_id:
            return
        
        # Get user data
        email = None
        phone = None
        if request.user.is_authenticated:
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
                "client_ip_address": self._get_client_ip(request),
                "client_user_agent": request.META.get('HTTP_USER_AGENT', ''),
            },
            "event_data": event_data or {},
        }
        
        # Send event via API (Server-side tracking)
        self._send_event(event)
        
        # Also push to client-side
        self._push_client_event(event_name, event_data, user_data)
    
    def _send_event(self, event):
        """Send event to TikTok Business API (Server-side)"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Access-Token": settings.TIKTOK_ACCESS_TOKEN,
            }
            payload = {
                "pixel_id": self.pixel_id,
                "events": [event],
                "test_event_code": getattr(settings, 'TIKTOK_TEST_EVENT_CODE', ''),
            }
            response = requests.post(self.api_base, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"✅ TikTok Pixel event sent: {event['event_name']}")
            else:
                print(f"❌ TikTok Pixel error: {response.text}")
        except Exception as e:
            print(f"❌ TikTok Pixel exception: {e}")
    
    def _push_client_event(self, event_name, event_data, user_data):
        """Push event to client-side JavaScript"""
        # This will be handled by the template's JavaScript
    
    def _hash(self, value):
        """Hash user data for TikTok"""
        import hashlib
        if not value:
            return ""
        return hashlib.md5(value.lower().strip().encode()).hexdigest()
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# Singleton instance
tiktok_pixel = TikTokPixel()

def track_tiktok_event(request, event_name, event_data=None, user_data=None):
    """Helper function to track TikTok events"""
    tiktok_pixel.track_event(request, event_name, event_data, user_data)