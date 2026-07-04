# lacesstore/middleware.py
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from .models import Visitor, DailyVisitorStats
from django.contrib.auth.models import User

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    # def __call__(self, request):
    #     # Skip tracking for admin, static files, and API calls
    #     if not request.path.startswith('/admin') and not request.path.startswith('/static'):
    #         self.track_visitor(request)
        
    #     response = self.get_response(request)
    #     return response
    
    def __call__(self, request):
        # Send PageView to Facebook CAPI
        if not request.path.startswith('/admin') and not request.path.startswith('/static'):
            try:
                from .facebook_capi import send_facebook_event
                send_facebook_event(request, 'PageView', {
                    'url': request.path,
                    'title': 'Page View'
                })
            except Exception as e:
                print(f"Facebook CAPI PageView error: {e}")
        
        response = self.get_response(request)
        return response



    def track_visitor(self, request):
        # Get or create session
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get visitor information
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
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