# core/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from .models import Ishchi, Sektor, Shobe, Departament

class PageAccessTestCase(TestCase):
    def setUp(self):
        """Testlərdən əvvəl hər dəfə işə düşən hazırlıq funksiyası."""
        self.client = Client()
        self.departament = Departament.objects.create(ad="Test Departamenti")
        self.shobe = Shobe.objects.create(ad="Test Şöbəsi", departament=self.departament)
        self.sektor = Sektor.objects.create(ad="Test Sektoru", shobe=self.shobe)
        self.normal_user = Ishchi.objects.create_user(
            username='testishchi', password='password123', rol='ISHCHI', sektor=self.sektor
        )
        self.superadmin_user = Ishchi.objects.create_user(
            username='testsuperadmin', password='password123', rol='SUPERADMIN', sektor=self.sektor, is_staff=True
        )

    def test_dashboard_unauthenticated_redirect(self):
        """Test 1: Giriş etməmiş istifadəçinin ana səhifədən login səhifəsinə yönləndirilməsi."""
        response = self.client.get(reverse('dashboard'))
        # Cavabın 302 (Redirect) olduğunu yoxlayırıq
        self.assertEqual(response.status_code, 302)
        
        # DÜZƏLİŞ: Yönləndirilən URL-in settings-dəki LOGIN_URL ilə başladığını yoxlayırıq.
        # Bu, daha çevik və düzgün bir yoxlamadır.
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_dashboard_authenticated_access(self):
        """Test 2: Giriş etmiş normal istifadəçinin ana səhifəyə daxil ola bilməsi."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

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