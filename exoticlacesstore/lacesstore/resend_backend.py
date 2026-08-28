# lacesstore/resend_backend.py
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from django.conf import settings

class ResendEmailBackend(BaseEmailBackend):
    """Email backend that uses Resend API instead of SMTP"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', '')
        self.api_url = "https://api.resend.com/emails"
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        
        print(f"✅ ResendEmailBackend initialized")
        
    def open(self):
        """No-op for API backend"""
        return True
        
    def close(self):
        """No-op for API backend"""
        pass
        
    def send_messages(self, email_messages):
        """Send emails using Resend API"""
        if not self.api_key:
            print("❌ RESEND_API_KEY is not configured")
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY is not configured")
            return 0
            
        sent_count = 0
        for message in email_messages:
            try:
                # ✅ Fix: Add encoding parameter to sanitize_address
                from_email = sanitize_address(message.from_email, 'utf-8') or self.from_email
                to_emails = [sanitize_address(addr, 'utf-8') for addr in message.to]
                
                if not from_email:
                    from_email = self.from_email
                
                # Prepare the email
                email_data = {
                    "from": from_email,
                    "to": to_emails,
                    "subject": message.subject,
                }
                
                # Add HTML content if available
                if message.alternatives:
                    for alt in message.alternatives:
                        if alt[1] == "text/html":
                            email_data["html"] = alt[0]
                            break
                elif message.body:
                    email_data["text"] = message.body
                
                # Add CC and BCC with encoding fix
                if message.cc:
                    email_data["cc"] = [sanitize_address(addr, 'utf-8') for addr in message.cc]
                if message.bcc:
                    email_data["bcc"] = [sanitize_address(addr, 'utf-8') for addr in message.bcc]
                
                # Add reply-to with encoding fix
                if message.reply_to:
                    email_data["reply_to"] = [sanitize_address(addr, 'utf-8') for addr in message.reply_to]
                
                # Send via Resend API
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                print(f"📧 Sending email via Resend API to: {to_emails}")
                
                response = requests.post(self.api_url, json=email_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    sent_count += 1
                    print(f"✅ Email sent successfully via Resend API")
                else:
                    print(f"❌ Resend API error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Email send error: {e}")
                if not self.fail_silently:
                    raise
                
        return sent_count