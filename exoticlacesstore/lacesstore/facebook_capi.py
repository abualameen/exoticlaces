# lacesstore/facebook_capi.py
import hashlib
import time
import requests
from django.conf import settings
from django.contrib.auth.models import User

def get_facebook_user_data(user):
    """Format user data for Facebook CAPI"""
    user_data = {}
    
    if user and user.email:
        # Hash the email (required for CAPI)
        user_data['em'] = [hashlib.sha256(user.email.encode('utf-8')).hexdigest()]
    
    # Add phone if available
    if hasattr(user, 'customer') and user.customer.phonenumber:
        phone = str(user.customer.phonenumber)
        user_data['ph'] = [hashlib.sha256(phone.encode('utf-8')).hexdigest()]
    
    # Add IP address and user agent (will be passed from request)
    return user_data

def send_facebook_event(request, event_name, custom_data=None):
    """
    Send a Facebook CAPI event from the server side
    """
    pixel_id = settings.FACEBOOK_PIXEL_ID
    access_token = settings.FACEBOOK_CAPI_ACCESS_TOKEN
    
    if not access_token:
        print("Facebook CAPI token not configured")
        return False
    
    # Get user data from request
    user_data = {}
    if request.user.is_authenticated:
        user_data = get_facebook_user_data(request.user)
    
    # Add client IP and user agent
    user_data['client_ip_address'] = request.META.get('REMOTE_ADDR', '')
    user_data['client_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    # Build the event
    event_data = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "user_data": user_data,
            "custom_data": custom_data or {},
            "action_source": "website"
        }]
    }
    
    # Send to Facebook
    url = f"https://graph.facebook.com/v18.0/{pixel_id}/events"
    params = {"access_token": access_token}
    
    try:
        response = requests.post(url, params=params, json=event_data)
        result = response.json()
        if response.status_code == 200:
            print(f"✅ Facebook CAPI event sent: {event_name}")
            return True
        else:
            print(f"❌ Facebook CAPI error: {result}")
            return False
    except Exception as e:
        print(f"❌ Facebook CAPI exception: {e}")
        return False