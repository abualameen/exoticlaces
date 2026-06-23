# lacesstore/email_backend.py
import socket
import time
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.utils import DNS_NAME
from smtplib import SMTP, SMTP_SSL

class RetryEmailBackend(EmailBackend):
    """Email backend that tries multiple ports and retries on failure"""
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None,
                 **kwargs):
        # Initialize the parent class
        super().__init__(host=host, port=port, username=username,
                        password=password, use_tls=use_tls,
                        fail_silently=fail_silently, use_ssl=use_ssl,
                        timeout=timeout, ssl_keyfile=ssl_keyfile,
                        ssl_certfile=ssl_certfile, **kwargs)
        
        # Define port alternatives
        self.port_alternatives = [587, 465, 2525, 25]
        self.connection_failed = False
        
        # Ensure local_hostname is set
        if not hasattr(self, 'local_hostname'):
            self.local_hostname = None
    
    def open(self):
        """
        Ensure we have a connection to the email server.
        Try multiple ports if the default fails.
        """
        if self.connection:
            return False
        
        # Get local_hostname from parent if available
        if not hasattr(self, 'local_hostname'):
            self.local_hostname = None
        
        # Try the primary port first
        try:
            return self._try_connect(self.port)
        except Exception as e:
            print(f"Primary port {self.port} failed: {e}")
            # Try alternative ports
            for alt_port in self.port_alternatives:
                if alt_port == self.port:
                    continue
                print(f"Trying alternative port: {alt_port}")
                try:
                    if self._try_connect(alt_port):
                        # Save the working port for future use
                        self.port = alt_port
                        print(f"✅ Using port {alt_port}")
                        return True
                except Exception as alt_e:
                    print(f"Port {alt_port} failed: {alt_e}")
                    continue
        
        if not self.fail_silently:
            raise
        return False
    
    def _try_connect(self, port):
        """Attempt to connect to the email server on a specific port"""
        self.port = port
        
        # Reset connection
        if self.connection:
            self.close()
        
        # Determine if SSL should be used
        use_ssl = port in [465, 995, 25]  # Common SSL ports
        
        # Create connection
        try:
            if use_ssl:
                self.connection = SMTP_SSL(
                    self.host, self.port,
                    timeout=self.timeout,
                    keyfile=self.ssl_keyfile,
                    certfile=self.ssl_certfile,
                )
            else:
                self.connection = SMTP(
                    self.host, self.port,
                    timeout=self.timeout,
                )
            
            # Identify ourselves
            self.connection.ehlo_or_helo_if_needed()
            
            # Use TLS if enabled (and not using SSL)
            if self.use_tls and not use_ssl:
                self.connection.starttls(
                    keyfile=self.ssl_keyfile,
                    certfile=self.ssl_certfile,
                )
                self.connection.ehlo_or_helo_if_needed()
            
            # Login if credentials provided
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
            
        except Exception as e:
            if self.connection:
                self.close()
            raise e