# core/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from .models import Ishchi, Sektor, Shobe, Departament

class PageAccessTestCase(TestCase):
    def setUp(self):
        """Testlərdən əvvəl hər dəfə işə düşən hazırlıq funksiyası."""
        # Test üçün lazım olan obyektləri yaradırıq
        self.client = Client()
        
        # Test üçün departament, şöbə və sektor yaradırıq
        self.departament = Departament.objects.create(ad="Test Departamenti")
        self.shobe = Shobe.objects.create(ad="Test Şöbəsi", departament=self.departament)
        self.sektor = Sektor.objects.create(ad="Test Sektoru", shobe=self.shobe)

        # Test üçün fərqli rollarda istifadəçilər yaradırıq
        self.normal_user = Ishchi.objects.create_user(
            username='testishchi', 
            password='password123', 
            rol='ISHCHI', 
            sektor=self.sektor
        )
        self.superadmin_user = Ishchi.objects.create_user(
            username='testsuperadmin', 
            password='password123', 
            rol='SUPERADMIN', 
            sektor=self.sektor,
            is_staff=True # Admin panelinə giriş üçün
        )

    def test_dashboard_unauthenticated_redirect(self):
        """Test 1: Giriş etməmiş istifadəçinin ana səhifədən login səhifəsinə yönləndirilməsi."""
        response = self.client.get(reverse('dashboard'))
        # Gözləyirik ki, cavab 302 (Redirect) status kodu ilə qayıtsın və login səhifəsinə yönlənsin
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_dashboard_authenticated_access(self):
        """Test 2: Giriş etmiş normal istifadəçinin ana səhifəyə daxil ola bilməsi."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('dashboard'))
        # Gözləyirik ki, səhifə uğurla açılsın (200 OK)
        self.assertEqual(response.status_code, 200)

    def test_superadmin_panel_permission_denied_for_normal_user(self):
        """Test 3: Normal istifadəçinin superadmin panelinə girişinin qadağan edilməsi."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('superadmin_paneli'))
        # Gözləyirik ki, sistem 403 (Forbidden) xətası versin
        self.assertEqual(response.status_code, 403)

    def test_superadmin_panel_access_for_superadmin_user(self):
        """Test 4: Superadmin roluna malik istifadəçinin superadmin panelinə daxil ola bilməsi."""
        self.client.login(username='testsuperadmin', password='password123')
        response = self.client.get(reverse('superadmin_paneli'))
        # Gözləyirik ki, səhifə uğurla açılsın (200 OK)
        self.assertEqual(response.status_code, 200)