# core/tests.py - BÜTÜN MODULLARI ƏHATƏ EDƏN TEST DƏSTİ

import re
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core import mail # E-poçtları test etmək üçün
from .models import (
    Ishchi, Sektor, Shobe, Departament, 
    QiymetlendirmeDovru, InkishafPlani, Hedef
)

# Testləri qruplaşdırmaq üçün ümumi bir "hazırlıq" sinfi
class BaseTestCase(TestCase):
    def setUp(self):
        """Bütün test sinifləri üçün ortaq olan hazırlıq."""
        self.client = Client()
        self.departament = Departament.objects.create(ad="Test Departamenti")
        self.shobe = Shobe.objects.create(ad="Test Şöbəsi", departament=self.departament)
        self.sektor = Sektor.objects.create(ad="Test Sektoru", shobe=self.shobe)

        self.normal_user = Ishchi.objects.create_user(
            username='testishchi', 
            password='password123', 
            email='ishchi@example.com',
            rol='ISHCHI', 
            sektor=self.sektor,
            first_name="Test", last_name="İşçi"
        )
        self.superadmin_user = Ishchi.objects.create_user(
            username='testsuperadmin', 
            password='password123', 
            rol='SUPERADMIN', 
            sektor=self.sektor,
            is_staff=True, is_superuser=True
        )

# --- Test Sinif 1: Səhifəyə Giriş İcazələri ---
class PageAccessTests(BaseTestCase):

    def test_dashboard_unauthenticated_redirect(self):
        """Test 1: Giriş etməmiş istifadəçinin ana səhifədən login səhifəsinə yönləndirilməsi."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_dashboard_authenticated_access(self):
        """Test 2: Giriş etmiş normal istifadəçinin ana səhifəyə daxil ola bilməsi."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Qiymətləndirmə Tapşırıqlarınız")

    def test_superadmin_panel_permission_denied_for_normal_user(self):
        """Test 3: Normal istifadəçinin superadmin panelinə girişinin qadağan edilməsi."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(response.status_code, 403)

    def test_superadmin_panel_access_for_superadmin_user(self):
        """Test 4: Superadmin roluna malik istifadəçinin superadmin panelinə daxil ola bilməsi."""
        self.client.login(username='testsuperadmin', password='password123')
        response = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(response.status_code, 200)


# --- Test Sinif 2: Autentifikasiya Axınları (Login, Register, Password Reset) ---
class AuthenticationFlowsTests(BaseTestCase):

    def test_successful_registration(self):
        """Test 5: Yeni istifadəçinin qeydiyyatdan uğurla keçməsi."""
        user_count_before = Ishchi.objects.count()
        response = self.client.post(reverse('qeydiyyat'), {
            'username': 'yeniistifadechi',
            'first_name': 'Yeni',
            'last_name': 'İstifadəçi',
            'email': 'yeni@example.com',
            'sektor': self.sektor.id,
            'password1': 'GucluShifre123',
            'password2': 'GucluShifre123',
        })
        # Uğurlu qeydiyyatdan sonra ana səhifəyə yönləndirilməlidir
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        # İstifadəçi sayının bir vahid artdığını yoxlayırıq
        self.assertEqual(Ishchi.objects.count(), user_count_before + 1)

    def test_login_with_email(self):
        """Test 6: İstifadəçinin həm istifadəçi adı, həm də e-poçt ilə daxil ola bilməsi."""
        # E-poçt ilə giriş
        login_successful = self.client.login(username='ishchi@example.com', password='password123')
        self.assertTrue(login_successful)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # İstifadəçi adı ilə giriş
        login_successful = self.client.login(username='testishchi', password='password123')
        self.assertTrue(login_successful)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_flow(self):
        """Test 7: Şifrə bərpası axınının tam olaraq işləməsi."""
        # Addım 1: Şifrə bərpası tələbi göndəririk
        self.client.post(reverse('password_reset'), {'email': 'ishchi@example.com'})
        
        # Addım 2: E-poçtun göndərildiyini yoxlayırıq (konsola yazılır)
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to[0], 'ishchi@example.com')
        
        # Addım 3: E-poçtdan bərpa linkini tapırıq
        url_match = re.search(r'http://testserver(/accounts/reset/[^/]+/[^/]+/)\s', sent_email.body)
        self.assertIsNotNone(url_match)
        reset_url = url_match.group(1)

        # Addım 4: Yeni şifrə təyin etmə səhifəsinə POST sorğusu göndəririk
        response = self.client.post(reset_url, {
            'new_password1': 'yeniGucluShifre456',
            'new_password2': 'yeniGucluShifre456',
        })

        # Addım 5: Uğurlu dəyişiklikdən sonra yönləndirməni yoxlayırıq
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_reset_complete'))

        # Addım 6: Yeni şifrə ilə daxil olmağı yoxlayırıq
        login_successful = self.client.login(username='testishchi', password='yeniGucluShifre456')
        self.assertTrue(login_successful)