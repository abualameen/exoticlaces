# lacesstore/facebook_capi.py
import hashlib
import time
import requests
from django.conf import settings
import uuid

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
    
    return user_data

# def send_facebook_event(request, event_name, custom_data=None):
#     """
#     Send a Facebook CAPI event from the server side
#     """
#     pixel_id = settings.FACEBOOK_PIXEL_ID
#     access_token = settings.FACEBOOK_CAPI_ACCESS_TOKEN
    
#     if not access_token:
#         print("❌ Facebook CAPI token not configured")
#         return False
    
#     # ✅ Get user data from request
#     user_data = {}
    
#     # ✅ Add email from authenticated user
#     if request.user.is_authenticated and request.user.email:
#         user_data['em'] = [hashlib.sha256(request.user.email.encode('utf-8')).hexdigest()]
    
#     # ✅ Add phone number if available
#     if hasattr(request.user, 'customer') and request.user.customer.phonenumber:
#         phone = str(request.user.customer.phonenumber)
#         user_data['ph'] = [hashlib.sha256(phone.encode('utf-8')).hexdigest()]
    
#     # ✅ Add client IP and user agent
#     user_data['client_ip_address'] = request.META.get('REMOTE_ADDR', '')
#     user_data['client_user_agent'] = request.META.get('HTTP_USER_AGENT', '')

#     # ✅ Get Click ID (fbc) from cookies
#     fbc = request.COOKIES.get('_fbc')
#     if fbc:
#         user_data['fbc'] = fbc
    
#     # ✅ Get Browser ID (fbp) from cookies
#     fbp = request.COOKIES.get('_fbp')
#     if fbp:
#         user_data['fbp'] = fbp
    
#     # ✅ Add first name and last name if available
#     if request.user.is_authenticated:
#         if request.user.first_name:
#             user_data['fn'] = [hashlib.sha256(request.user.first_name.encode('utf-8')).hexdigest()]
#         if request.user.last_name:
#             user_data['ln'] = [hashlib.sha256(request.user.last_name.encode('utf-8')).hexdigest()]
    
#     # Build the event
#     event_data = {
#         "data": [{
#             "event_name": event_name,
#             "event_time": int(time.time()),
#             "user_data": user_data,
#             "custom_data": custom_data or {},
#             "action_source": "website",
#             "test_event_code": "TEST1940"
#         }]
#     }
    
#     # Send to Facebook
#     url = f"https://graph.facebook.com/v18.0/{pixel_id}/events"
#     params = {"access_token": access_token}
    
#     try:
#         response = requests.post(url, params=params, json=event_data)
#         result = response.json()
#         if response.status_code == 200:
#             print(f"✅ Facebook CAPI event sent: {event_name}")
#             print(f"📊 User data sent: {list(user_data.keys())}")
#             return True
#         else:
#             print(f"❌ Facebook CAPI error: {result}")
#             return False
#     except Exception as e:
#         print(f"❌ Facebook CAPI exception: {e}")
#         return False



# lacesstore/facebook_capi.py
def send_facebook_event(request, event_name, custom_data=None):
    """
    Send a Facebook CAPI event from the server side
    """
    pixel_id = settings.FACEBOOK_PIXEL_ID
    access_token = settings.FACEBOOK_CAPI_ACCESS_TOKEN
    
    if not access_token:
        print("❌ Facebook CAPI token not configured")
        return False
    
    # ✅ Get user data from request
    user_data = {}
    
    # ✅ Add email from authenticated user OR from session/checkout data
    email = None
    if request.user.is_authenticated and request.user.email:
        email = request.user.email
    else:
        # Try to get email from session (guest checkout)
        checkout_data = request.session.get('checkout_data', {})
        email = checkout_data.get('email')
    
    if email:
        user_data['em'] = [hashlib.sha256(email.encode('utf-8')).hexdigest()]
    
    # ✅ Add client IP and user agent (works for everyone)
    user_data['client_ip_address'] = request.META.get('REMOTE_ADDR', '')
    user_data['client_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    # ✅ Get Click ID (fbc) from cookies (works for everyone)
    fbc = request.COOKIES.get('_fbc')
    if fbc:
        user_data['fbc'] = fbc
    
    # ✅ Get Browser ID (fbp) from cookies (works for everyone)
    fbp = request.COOKIES.get('_fbp')
    if fbp:
        user_data['fbp'] = fbp
    
    # ✅ Add first name and last name if available
    if request.user.is_authenticated:
        if request.user.first_name:
            user_data['fn'] = [hashlib.sha256(request.user.first_name.encode('utf-8')).hexdigest()]
        if request.user.last_name:
            user_data['ln'] = [hashlib.sha256(request.user.last_name.encode('utf-8')).hexdigest()]
    else:
        # Try to get from session for guests
        checkout_data = request.session.get('checkout_data', {})
        if checkout_data.get('firstName'):
            user_data['fn'] = [hashlib.sha256(checkout_data.get('firstName', '').encode('utf-8')).hexdigest()]
        if checkout_data.get('lastName'):
            user_data['ln'] = [hashlib.sha256(checkout_data.get('lastName', '').encode('utf-8')).hexdigest()]
    
    # Build the event
    if not event_id:
        event_id = str(uuid.uuid4())  # Generate unique ID
    
    # Build the event
    event_data = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "event_id": event_id,  # ✅ Add this line
            "user_data": user_data,
            "custom_data": custom_data or {},
            "action_source": "website",
            "test_event_code": "TEST1940"
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
            print(f"📊 User data sent: {list(user_data.keys())}")
            return True
        else:
            print(f"❌ Facebook CAPI error: {result}")
            return False
    except Exception as e:
        print(f"❌ Facebook CAPI exception: {e}")
        return False