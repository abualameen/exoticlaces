# lacesstore/middleware.py
import re
from django.utils.deprecation import MiddlewareMixin
import time  # ✅ ADD THIS - was missing!
from django.utils import timezone
from django.core.cache import cache
from django.http import HttpResponse
from .models import Visitor, DailyVisitorStats

# ✅ BOT PATTERNS - Expanded but not the only defense
BOT_PATTERNS = [
    # ... (keep all your existing patterns) ...
    r'bot', r'crawler', r'spider', r'scraper',
    r'curl', r'wget', r'headless', r'phantom',
    r'selenium', r'puppeteer', r'webdriver',
    r'python-requests', r'http-client', r'go-http-client',
    r'urllib', r'requests', r'httpx', r'aiohttp',
    r'axios', r'fetch', r'node-fetch', r'scrapy',
    r'obbidian', r'TLM-Audit-Scanner', r'pathscan',
    r'SERanKingBacklinksBot', r'SecurityResearch',
    r'MSIE', r'rv:14', r'Chrome/[0-9][0-9]\.',
    r'facebookexternalhit', r'Twitterbot',
    r'GPTBot', r'ClaudeBot', r'Bytespider',
    r'wp-admin', r'wp-json', r'xmlrpc', r'WordPress',
    r'^$',  # Empty user-agent
]

# Rate limit: 30 requests per minute per IP
RATE_LIMIT = 30
RATE_WINDOW = 60  # seconds

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_rate_limited(ip):
    """Check if IP is rate limited"""
    cache_key = f"rate_limit_{ip}"
    current = int(time.time())
    
    requests = cache.get(cache_key, [])
    requests = [t for t in requests if current - t < RATE_WINDOW]
    
    if len(requests) >= RATE_LIMIT:
        return True
    
    requests.append(current)
    cache.set(cache_key, requests, timeout=RATE_WINDOW + 10)
    return False

def is_bot(request):
    """Enhanced bot detection with multiple layers"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip = get_client_ip(request)
    
    # ✅ LAYER 1: Check user-agent patterns
    if not user_agent or len(user_agent) < 10:
        return True
    
    user_agent_lower = user_agent.lower()
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower, re.IGNORECASE):
            return True
    
    # ✅ LAYER 2: Check rate limiting
    if is_rate_limited(ip):
        return True
    
    # ✅ LAYER 3: Check for JavaScript cookie (real browsers)
    if not request.COOKIES.get('js_enabled'):
        return True
    
    # ✅ LAYER 4: Check request patterns
    suspicious_paths = ['/wp-', '/xmlrpc', '/.env', '/config', '/backup']
    for path in suspicious_paths:
        if request.path.lower().startswith(path):
            return True
    
    return False

class VisitorTrackingMiddleware(MiddlewareMixin):
    """Middleware to track unique visitors and filter out bots"""
    
    def process_request(self, request):
        # ✅ Skip admin, static, media, and API paths
        skip_paths = ['/admin', '/static', '/media', '/api', '/favicon.ico', '/robots.txt']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # ✅ JAVASCRIPT CHALLENGE - Returns a page that requires JS
        if not request.COOKIES.get('js_enabled') and not request.path.startswith('/_'):
            return HttpResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="robots" content="noindex, nofollow">
                <title>Verifying...</title>
                <style>
                    body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f5f5f5; }
                    .loader { border: 4px solid #f3f3f3; border-top: 4px solid #8B4513; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div style="text-align: center; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div class="loader"></div>
                    <p style="margin-top: 20px; color: #333;">Verifying your browser...</p>
                    <script>
                        document.cookie = "js_enabled=1; path=/; max-age=3600";
                        window.location.reload();
                    </script>
                </div>
            </body>
            </html>
            """, content_type='text/html')
        
        # ✅ Skip if it's a bot
        if is_bot(request):
            return None
        
        # ✅ Track real visitors
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
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
        
        # ✅ Fire Facebook CAPI event
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