# lacesstore/middleware.py
from django.utils.timezone import now
from .models import Visitor
import re

# Comprehensive bot patterns
BOT_PATTERNS = [
    # Search engines
    r'googlebot',
    r'bingbot',
    r'slurp',
    r'duckduckbot',
    r'baiduspider',
    r'yandexbot',
    r'sogou',
    r'exabot',
    r'facebot',
    r'facebookexternalhit',
    r'twitterbot',
    r'linkedinbot',
    r'pinterestbot',
    r'slackbot',
    r'discordbot',
    r'telegrambot',
    r'whatsapp',
    
    # Generic bots
    r'bot',
    r'crawler',
    r'spider',
    r'scraper',
    r'curl',
    r'wget',
    r'python-requests',
    r'http-client',
    r'java/',
    r'okhttp',
    r'go-http-client',
    r'headless',
    r'phantomjs',
    r'selenium',
    r'puppeteer',
    
    # Monitoring services
    r'pingdom',
    r'uptimerobot',
    r'statuscake',
    r'newrelic',
    r'datadog',
    r'grafana',
    r'prometheus',
    
    # Cloud providers
    r'amazonaws',
    r'cloudflare',
    r'googlecloud',
    r'azure',
    r'digitalocean',
    
    # Other
    r'feedfetcher',
    r'pulse',
    r'subscriptions',
    r'readability',
    r'instapaper',
    r'pocket',
]

# Known bot IP ranges (add as needed)
BOT_IP_PATTERNS = [
    r'^66\.249\.',    # Googlebot
    r'^157\.55\.',    # Bing
    r'^40\.77\.',     # Bing
    r'^207\.46\.',    # Bing
    r'^52\.\d+\.\d+\.\d+',  # AWS
    r'^54\.\d+\.\d+\.\d+',  # AWS
    r'^35\.\d+\.\d+\.\d+',  # Google Cloud
    r'^34\.\d+\.\d+\.\d+',  # Google Cloud
]


def is_bot(user_agent, ip=None):
    """Check if the request is from a bot"""
    
    # Check user agent
    if not user_agent:
        return True  # No user agent = likely a bot
    
    user_agent_lower = user_agent.lower()
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    
    # Check IP if provided
    if ip:
        for pattern in BOT_IP_PATTERNS:
            if re.search(pattern, ip):
                return True
    
    return False


class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin') and not request.path.startswith('/static'):
            self.track_visitor(request)
            
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
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip = self.get_client_ip(request)
        
        # ✅ Enhanced bot detection
        if is_bot(user_agent, ip):
            return
        
        # Get or create session
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
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
        
        if not created:
            visitor.visit_count += 1
            visitor.last_visit = now()
            visitor.save()
        else:
            visitor.ip_address = ip
            visitor.user_agent = user_agent
            visitor.referer = referer
            visitor.save()
        
        if request.user.is_authenticated:
            visitor.user = request.user
            visitor.save()
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip