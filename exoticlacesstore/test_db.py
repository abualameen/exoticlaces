# test_db.py
import os
import django

# Manually set the password
os.environ['DB_PASSWORD'] = 'April_1985@'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exoticlacesstore.settings')
django.setup()

from django.conf import settings
from django.db import connection

print("="*50)
print("MySQL Connection Test")
print("="*50)
print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Name: {settings.DATABASES['default']['NAME']}")
print(f"User: {settings.DATABASES['default']['USER']}")
print(f"Password: {settings.DATABASES['default']['PASSWORD']}")

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✓ Basic query successful!")
        
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        print(f"✓ Connected to database: {db_name[0]}")
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ MySQL Version: {version[0]}")
        
        print("\n✓ All tests passed! MySQL is working correctly.")
        
except Exception as e:
    print(f"\n✗ Test failed: {e}")