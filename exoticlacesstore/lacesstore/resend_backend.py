# lacesstore/resend_backend.py
import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from django.conf import settings

class ResendEmailBackend(BaseEmailBackend):
    """Email backend that uses Resend API instead of SMTP"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', '')
        
        # ✅ Initialize Resend client
        if self.api_key:
            resend.api_key = self.api_key
        
    def send_messages(self, email_messages):
        """Send emails using Resend API"""
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY is not configured")
            return 0
            
        sent_count = 0
        for message in email_messages:
            try:
                # ✅ Extract email parts
                from_email = sanitize_address(message.from_email)
                to_emails = [sanitize_address(addr) for addr in message.to]
                
                # ✅ Prepare the email
                email_data = {
                    "from": from_email,
                    "to": to_emails,
                    "subject": message.subject,
                }
                
                # ✅ Add HTML content if available
                if message.alternatives:
                    for alt in message.alternatives:
                        if alt[1] == "text/html":
                            email_data["html"] = alt[0]
                            break
                else:
                    email_data["text"] = message.body
                
                # ✅ Add CC and BCC
                if message.cc:
                    email_data["cc"] = [sanitize_address(addr) for addr in message.cc]
                if message.bcc:
                    email_data["bcc"] = [sanitize_address(addr) for addr in message.bcc]
                
                # ✅ Add reply-to
                if message.reply_to:
                    email_data["reply_to"] = [sanitize_address(addr) for addr in message.reply_to]
                
                # ✅ Send via Resend API
                response = resend.Emails.send(email_data)
                
                if response and response.get('id'):
                    sent_count += 1
                    print(f"✅ Email sent successfully via Resend API (ID: {response['id']})")
                else:
                    print(f"❌ Resend API error: {response}")
                    
            except Exception as e:
                if not self.fail_silently:
                    raise
                print(f"❌ Email send error: {e}")
                
        return sent_count