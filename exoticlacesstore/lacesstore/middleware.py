# lacesstore/middleware.py
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from .models import Visitor, DailyVisitorStats
from django.contrib.auth.models import User
import re

# Common bot user agents
BOT_PATTERNS = [
    r'bot',
    r'crawler',
    r'spider',
    r'googlebot',
    r'facebookexternalhit',
    r'facebot',
    r'twitterbot',
    r'linkedinbot',
    r'Slackbot',
    r'Pingdom',
    r'UptimeRobot',
    r'StatusCake',
    r'NewRelic',
    r'Datadog',
]

def is_bot(user_agent):
    """Check if the user agent belongs to a bot/crawler"""
    if not user_agent:
        return True  # No user agent = likely a bot
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent, re.IGNORECASE):
            return True
    return False


class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin') and not request.path.startswith('/static'):
            # Track visitor (with bot filtering)
            self.track_visitor(request)
            
            # Send PageView to Facebook CAPI with event_id
            try:
                from .facebook_capi import send_facebook_event
                import uuid
                event_id = str(uuid.uuid4())
                send_facebook_event(
                    request, 
                    'PageView', 
                    {
                        'url': request.path,
                        'title': 'Page View'
                    },
                    event_id=event_id
                )
            except Exception as e:
                print(f"Facebook CAPI PageView error: {e}")
        
        response = self.get_response(request)
        return response

    def track_visitor(self, request):
        # Skip bots
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if is_bot(user_agent):
            return
        
        # Get or create session
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get visitor information
        ip = self.get_client_ip(request)
        referer = request.META.get('HTTP_REFERER', '')
        
        # Get or create visitor
        visitor, created = Visitor.objects.get_or_create(
            session_key=session_key,
            defaults={
                'ip_address': ip,
                'user_agent': user_agent,
                'referer': referer,
            }
        )
        
        # Update visitor
        if not created:
            visitor.visit_count += 1
            visitor.last_visit = now()
            visitor.save()
        else:
            # Update first visit with more info
            visitor.ip_address = ip
            visitor.user_agent = user_agent
            visitor.referer = referer
            visitor.save()
        
        # Link user if authenticated
        if request.user.is_authenticated:
            visitor.user = request.user
            visitor.save()
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip