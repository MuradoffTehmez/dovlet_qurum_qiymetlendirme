# core/tests/test_api.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from core.models import OrganizationUnit, QiymetlendirmeDovru, Notification

User = get_user_model()


class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            rol=User.Rol.ISHCHI
        )

    def test_token_obtain(self):
        """JWT token alınmasını test et"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_token_obtain_invalid_credentials(self):
        """Yanlış kimlik məlumatları ilə token alınmasını test et"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_without_token(self):
        """Token olmadan qorunan endpoint-ə müraciəti test et"""
        url = '/api/v1/users/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_token(self):
        """Token ilə qorunan endpoint-ə müraciəti test et"""
        # Token al
        token_url = reverse('token_obtain_pair')
        token_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        token_response = self.client.post(token_url, token_data)
        token = token_response.data['access']
        
        # Token ilə API-a müraciət et
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = '/api/v1/users/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserAPITest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            rol=User.Rol.ADMIN
        )
        
        self.regular_user = User.objects.create_user(
            username="user",
            email="user@example.com", 
            password="userpass123",
            rol=User.Rol.ISHCHI
        )

    def authenticate_user(self, user):
        """İstifadəçini authenticate et"""
        token_url = reverse('token_obtain_pair')
        token_data = {
            'username': user.username,
            'password': 'adminpass123' if user.rol == User.Rol.ADMIN else 'userpass123'
        }
        token_response = self.client.post(token_url, token_data)
        token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_user_list_as_admin(self):
        """Admin kimi istifadəçi siyahısını əldə etməyi test et"""
        self.authenticate_user(self.admin_user)
        
        url = '/api/v1/users/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) >= 2)

    def test_user_profile(self):
        """İstifadəçi profilini əldə etməyi test et"""
        self.authenticate_user(self.regular_user)
        
        url = '/api/v1/users/profile/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user')

    def test_user_create(self):
        """Yeni istifadəçi yaratmağı test et"""
        self.authenticate_user(self.admin_user)
        
        url = '/api/v1/users/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'rol': 'ISHCHI'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)


class DashboardAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            rol=User.Rol.ADMIN
        )
        
        # Test datası yarat
        self.dovr = QiymetlendirmeDovru.objects.create(
            ad="Test Dövrü",
            bashlama_tarixi=date.today(),
            bitme_tarixi=date.today() + timedelta(days=30),
            aktivdir=True
        )

    def authenticate_user(self):
        """İstifadəçini authenticate et"""
        token_url = reverse('token_obtain_pair')
        token_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        token_response = self.client.post(token_url, token_data)
        token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_dashboard_stats(self):
        """Dashboard statistikalarını test et"""
        self.authenticate_user()
        
        url = '/api/v1/dashboard/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Gözlənilən sahələrin olduğunu yoxla
        expected_fields = [
            'pending_evaluations',
            'completed_evaluations', 
            'unread_notifications',
            'quick_feedback_received',
            'ideas_submitted'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)
            self.assertIsInstance(response.data[field], int)


class OrganizationUnitAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            rol=User.Rol.ADMIN
        )
        
        self.parent_unit = OrganizationUnit.objects.create(
            name="Ana Şirkət",
            type=OrganizationUnit.UnitType.ALI_IDARE
        )
        
        self.child_unit = OrganizationUnit.objects.create(
            name="İT Departamenti",
            type=OrganizationUnit.UnitType.SHOBE,
            parent=self.parent_unit
        )

    def authenticate_user(self):
        """İstifadəçini authenticate et"""
        token_url = reverse('token_obtain_pair')
        token_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        token_response = self.client.post(token_url, token_data)
        token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_organization_unit_list(self):
        """Təşkilati vahidlər siyahısını test et"""
        self.authenticate_user()
        
        url = '/api/v1/organization-units/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_organization_unit_children(self):
        """Təşkilati vahidin alt vahidlərini test et"""
        self.authenticate_user()
        
        url = f'/api/v1/organization-units/{self.parent_unit.id}/children/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'İT Departamenti')


class NotificationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.notification = Notification.objects.create(
            recipient=self.user,
            title="Test Bildirişi",
            message="Bu bir test bildirişidir.",
            notification_type=Notification.NotificationType.INFO
        )

    def authenticate_user(self):
        """İstifadəçini authenticate et"""
        token_url = reverse('token_obtain_pair')
        token_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        token_response = self.client.post(token_url, token_data)
        token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_notification_list(self):
        """İstifadəçinin bildirişlərini test et"""
        self.authenticate_user()
        
        url = '/api/v1/notifications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Bildirişi')

    def test_mark_notification_read(self):
        """Bildirişi oxunmuş kimi işarələməyi test et"""
        self.authenticate_user()
        
        url = f'/api/v1/notifications/{self.notification.id}/mark_read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Bildirişin oxunmuş olduğunu yoxla
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)