# lacesstore/middleware.py
import re
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import Visitor, DailyVisitorStats

# ✅ COMPREHENSIVE BOT PATTERNS - CATCHES ALL
BOT_PATTERNS = [
    # ===== SEARCH ENGINES =====
    r'googlebot', r'bingbot', r'slurp', r'duckduckbot',
    r'baiduspider', r'yandexbot', r'sogou', r'exabot',
    r'facebot', r'facebookexternalhit', r'twitterbot',
    r'linkedinbot', r'pinterestbot', r'slackbot',
    r'discordbot', r'telegrambot', r'whatsapp',
    
    # ===== GENERIC BOTS =====
    r'bot', r'crawler', r'spider', r'scraper',
    r'curl', r'wget', r'java/', r'php', r'ruby', r'perl',
    r'headless', r'phantomjs', r'selenium', r'puppeteer',
    r'webdriver', r'headlesschrome', r'headlessfirefox',
    
    # ===== HTTP CLIENTS =====
    r'python-requests', r'http-client', r'okhttp', r'go-http-client',
    r'urllib', r'requests', r'httpx', r'aiohttp',
    r'axios', r'fetch', r'node-fetch', r'scrapy',
    
    # ===== TOOLS & SCRAPERS =====
    r'obbidian', r'nutch', r'heritrix', r'scrape', r'scraping',
    r'TLM-Audit-Scanner', r'pathscan', r'scanner', r'scan',
    r'SERanKingBacklinksBot',
    r'SecurityResearch',
    r'MSIE',
    
    # ===== CHROME BOTS (FAKE) =====
    r'Chrome/91\.0\.4472\.114',
    r'Chrome/91\.',
    r'Chrome/103\.0\.5067\.93',
    r'Chrome/120\.',
    r'Chrome/[0-9][0-9]\.0\.',
    r'Chrome/[0-9][0-9]\.[0-9]+\.[0-9]+\.[0-9]+',
    
    # ===== FIREFOX BOTS (FAKE) =====
    r'rv:140\.',
    r'rv:14[0-9]\.',
    
    # ===== AI CRAWLERS =====
    r'GPTBot', r'ClaudeBot', r'Bytespider', r'ChatGPT',
    r'Google-Extended', r'CCBot', r'PerplexityBot',
    r'Claude-Web', r'FacebookBot', r'AppleBot',
    r'Amazonbot', r'Applebot', r'AhrefsBot',
    
    # ===== SECURITY SCANNERS =====
    r'wp-admin', r'wp-json', r'xmlrpc', r'wp-login',
    r'install\.php', r'\.env', r'config', r'backup',
    r'WordPress',
    
    # ===== MONITORING SERVICES =====
    r'pingdom', r'uptimerobot', r'statuscake',
    r'newrelic', r'datadog', r'grafana', r'prometheus',
    
    # ===== CLOUD PROVIDERS =====
    r'amazonaws', r'cloudflare', r'googlecloud',
    r'azure', r'digitalocean', r'aws-lambda',
    
    # ===== EMPTY USER-AGENT =====
    r'^$',
    
    # ===== HEADLESS BROWSERS =====
    r'headless', r'phantom', r'selenium',
    r'puppeteer', r'playwright',
]

# ✅ ADD THIS - Bot IP patterns (was missing!)
BOT_IP_PATTERNS = [
    r'^66\.249\.',    # Googlebot
    r'^157\.55\.',    # Bing
    r'^40\.77\.',     # Bing
    r'^207\.46\.',    # Bing
    r'^52\.\d+\.\d+\.\d+',  # AWS
    r'^54\.\d+\.\d+\.\d+',  # AWS
    r'^35\.\d+\.\d+\.\d+',  # Google Cloud
    r'^34\.\d+\.\d+\.\d+',  # Google Cloud
    r'^100\.\d+\.\d+\.\d+', # Cloudflare
    r'^104\.\d+\.\d+\.\d+', # Cloudflare
]

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_bot(request):
    """Enhanced bot detection"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip = get_client_ip(request)
    
    # 1. Check if user agent is a bot
    if not user_agent or len(user_agent) < 10:
        return True
    
    user_agent_lower = user_agent.lower()
    
    # Check against all patterns
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower, re.IGNORECASE):
            return True
    
    # 2. Check IP against bot IP patterns
    if ip:
        for pattern in BOT_IP_PATTERNS:
            if re.search(pattern, ip):
                return True
    
    # 3. Check for headless browser indicators
    if 'headless' in user_agent_lower or 'webdriver' in user_agent_lower:
        return True
    
    # 4. Check for suspicious user-agent patterns (additional)
    suspicious_patterns = [
        'compatible; MSIE',
        'rv:',
        'SecurityResearch',
        'SERanKingBacklinksBot',
    ]
    for pattern in suspicious_patterns:
        if pattern.lower() in user_agent_lower:
            return True
    
    return False

class VisitorTrackingMiddleware(MiddlewareMixin):
    """Middleware to track unique visitors and filter out bots"""
    
    def process_request(self, request):
        # ✅ Skip admin, static, media, and API paths
        skip_paths = ['/admin', '/static', '/media', '/api', '/favicon.ico', '/robots.txt']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
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