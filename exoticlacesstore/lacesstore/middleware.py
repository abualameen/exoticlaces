# lacesstore/middleware.py
import re
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import Visitor, DailyVisitorStats

# Comprehensive bot patterns (kept from your original)
BOT_PATTERNS = [
    # Search engines
    r'googlebot', r'bingbot', r'slurp', r'duckduckbot',
    r'baiduspider', r'yandexbot', r'sogou', r'exabot',
    r'facebot', r'facebookexternalhit', r'twitterbot',
    r'linkedinbot', r'pinterestbot', r'slackbot',
    r'discordbot', r'telegrambot', r'whatsapp',
    
    # Generic bots
    r'bot', r'crawler', r'spider', r'scraper',
    r'curl', r'wget', r'python-requests', r'http-client',
    r'java/', r'okhttp', r'go-http-client',
    r'headless', r'phantomjs', r'selenium', r'puppeteer',
    
    # AI crawlers (new)
    r'GPTBot', r'ClaudeBot', r'Bytespider', r'ChatGPT',
    r'Google-Extended', r'CCBot', r'PerplexityBot',
    
    # Monitoring services
    r'pingdom', r'uptimerobot', r'statuscake',
    r'newrelic', r'datadog', r'grafana', r'prometheus',
    
    # Cloud providers
    r'amazonaws', r'cloudflare', r'googlecloud',
    r'azure', r'digitalocean',
    
    # Other
    r'feedfetcher', r'pulse', r'subscriptions',
    r'readability', r'instapaper', r'pocket',
]

# Bot IP patterns
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
    # No user agent = bot
    if not user_agent:
        return True
    
    user_agent_lower = user_agent.lower()
    
    # Check user agent against patterns
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    
    # Check IP if provided
    if ip:
        for pattern in BOT_IP_PATTERNS:
            if re.search(pattern, ip):
                return True
    
    return False


class VisitorTrackingMiddleware(MiddlewareMixin):
    """Middleware to track unique visitors and filter out bots"""
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_request(self, request):
        # ✅ Skip admin, static, media, and API paths
        skip_paths = ['/admin', '/static', '/media', '/api', '/favicon.ico', '/robots.txt']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # ✅ Get user agent and IP
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip = self.get_client_ip(request)
        
        # ✅ Skip bot detection
        if is_bot(user_agent, ip):
            return None
        
        # ✅ Track real visitors
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        referer = request.META.get('HTTP_REFERER', '')
        
        # ✅ Get or create visitor
        visitor, created = Visitor.objects.get_or_create(
            session_key=session_key,
            defaults={
                'ip_address': ip,
                'user_agent': user_agent,
                'referer': referer,
                'user': request.user if request.user.is_authenticated else None,
            }
        )
        
        if not created:
            # ✅ Update existing visitor
            visitor.last_visit = timezone.now()
            visitor.visit_count += 1
            visitor.user_agent = user_agent
            visitor.referer = referer
            if request.user.is_authenticated:
                visitor.user = request.user
            visitor.save()
        else:
            # ✅ New visitor - update daily stats
            today = timezone.now().date()
            stats, _ = DailyVisitorStats.objects.get_or_create(date=today)
            stats.unique_visitors += 1
            if request.user.is_authenticated:
                stats.registered_users += 1
            else:
                stats.guest_users += 1
            stats.save()
        
        # ✅ Fire Facebook CAPI event (kept from your original)
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
        
        return None