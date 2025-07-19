#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('.')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

def test_admin_pages():
    """Quick test of admin functionality"""
    print("Testing admin access...")
    
    try:
        # Create test client
        client = Client()
        
        # Get OrganizationUnit admin URL
        changelist_url = reverse('admin:core_organizationunit_changelist')
        print(f"OrganizationUnit URL: {changelist_url}")
        
        # Access the page (should redirect to login)
        response = client.get(changelist_url)
        print(f"Response status: {response.status_code}")
        print(f"Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")
        
        # Check if we have superusers
        User = get_user_model()
        superusers = User.objects.filter(is_superuser=True)
        print(f"Available superusers: {superusers.count()}")
        
        if superusers.exists():
            # Login as superuser
            superuser = superusers.first()
            client.force_login(superuser)
            print(f"Logged in as: {superuser.username}")
            
            # Try accessing admin again
            response = client.get(changelist_url)
            print(f"After login status: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: OrganizationUnit admin page accessible!")
                return True
            else:
                print(f"ERROR: Status {response.status_code}")
                print(f"Content preview: {response.content[:200]}")
        else:
            print("No superusers available - creating one...")
            User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
            print("Superuser created. Try logging in with admin/admin123")
        
        return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_admin_pages()