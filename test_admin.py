#!/usr/bin/env python
"""
Test script to diagnose OrganizationUnit admin issues
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import OrganizationUnit
from django.contrib import admin

def test_admin_access():
    """Test if OrganizationUnit admin page is accessible"""
    print("=== OrganizationUnit Admin Diagnostic Test ===\n")
    
    # 1. Check if model is registered
    print("1. Checking admin registration...")
    is_registered = admin.site.is_registered(OrganizationUnit)
    print(f"   OrganizationUnit registered in admin: {is_registered}")
    
    if is_registered:
        admin_class = admin.site._registry[OrganizationUnit]
        print(f"   Admin class: {admin_class.__class__.__name__}")
    
    # 2. Check URL resolution
    print("\n2. Checking URL resolution...")
    try:
        changelist_url = reverse('admin:core_organizationunit_changelist')
        print(f"   Changelist URL: {changelist_url}")
        
        add_url = reverse('admin:core_organizationunit_add')
        print(f"   Add URL: {add_url}")
    except Exception as e:
        print(f"   ERROR resolving URLs: {e}")
        return False
    
    # 3. Check model data
    print("\n3. Checking model data...")
    try:
        count = OrganizationUnit.objects.count()
        print(f"   Total OrganizationUnit objects: {count}")
        
        if count > 0:
            first_obj = OrganizationUnit.objects.first()
            print(f"   First object: {first_obj}")
            print(f"   Object type: {first_obj.get_type_display()}")
            print(f"   Object parent: {first_obj.parent}")
    except Exception as e:
        print(f"   ERROR accessing model data: {e}")
    
    # 4. Test admin methods
    print("\n4. Testing admin methods...")
    try:
        from core.admin import OrganizationUnitAdmin
        admin_instance = OrganizationUnitAdmin(OrganizationUnit, admin.site)
        
        if count > 0:
            obj = OrganizationUnit.objects.first()
            
            # Test each admin method
            try:
                hierarchy = admin_instance.get_hierarchy_level(obj)
                print(f"   get_hierarchy_level: '{hierarchy}'")
            except Exception as e:
                print(f"   ERROR in get_hierarchy_level: {e}")
            
            try:
                emp_count = admin_instance.get_employees_count(obj)
                print(f"   get_employees_count: {emp_count}")
            except Exception as e:
                print(f"   ERROR in get_employees_count: {e}")
            
            try:
                children_count = admin_instance.get_children_count(obj)
                print(f"   get_children_count: {children_count}")
            except Exception as e:
                print(f"   ERROR in get_children_count: {e}")
                
    except Exception as e:
        print(f"   ERROR testing admin methods: {e}")
    
    # 5. Test HTTP access (simulate)
    print("\n5. Testing HTTP access simulation...")
    try:
        User = get_user_model()
        
        # Check if any superuser exists
        superusers = User.objects.filter(is_superuser=True)
        print(f"   Available superusers: {superusers.count()}")
        
        if superusers.exists():
            client = Client()
            
            # Try to login as first superuser
            superuser = superusers.first()
            login_success = client.force_login(superuser)
            print(f"   Force login with {superuser.username}: Success")
            
            # Try to access the admin changelist
            response = client.get(changelist_url)
            print(f"   Admin changelist response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response content preview: {response.content[:500]}")
        else:
            print("   No superusers available for testing")
            
    except Exception as e:
        print(f"   ERROR in HTTP access test: {e}")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    test_admin_access()