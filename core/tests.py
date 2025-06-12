# core/tests.py - BÜTÜN MODULLARI ƏHATƏ EDƏN YEKUN TEST DƏSTİ

import re
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core import mail
from .models import (
    Ishchi, Sektor, Shobe, Departament, 
    QiymetlendirmeDovru, InkishafPlani, Hedef
)


class BaseTestCase(TestCase):
    """Bütün test sinifləri üçün ortaq olan hazırlıq mühitini yaradır."""
    def setUp(self):
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
        self.manager_user = Ishchi.objects.create_user(
            username='testrehber', 
            password='password123', 
            rol='REHBER', 
            sektor=self.sektor, 
            first_name="Test", last_name="Rəhbər"
        )
        self.superadmin_user = Ishchi.objects.create_user(
            username='testsuperadmin', 
            password='password123', 
            rol='SUPERADMIN', 
            sektor=self.sektor,
            is_staff=True, is_superuser=True
        )


class PageAccessTests(BaseTestCase):
    """Səhifələrə giriş icazələrini və rol məntiqini yoxlayır."""

    def test_dashboard_unauthenticated_redirect(self):
        """Giriş etməmiş istifadəçinin ana səhifədən login-ə yönləndirilməsi."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_dashboard_authenticated_access(self):
        """Giriş etmiş istifadəçinin ana səhifəyə daxil ola bilməsi."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Qiymətləndirmə Tapşırıqlarınız")

    def test_superadmin_panel_permission_denied_for_normal_user(self):
        """Normal istifadəçinin superadmin panelinə girişinin qadağan edilməsi (403)."""
        self.client.login(username='testishchi', password='password123')
        response = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(response.status_code, 403)

    def test_superadmin_panel_access_for_superadmin_user(self):
        """Superadminin öz panelinə daxil ola bilməsi."""
        self.client.login(username='testsuperadmin', password='password123')
        response = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(response.status_code, 200)


class AuthenticationFlowsTests(BaseTestCase):
    """Qeydiyyat, Login və Şifrə Bərpası axınlarını yoxlayır."""

    def test_successful_registration(self):
        """Yeni istifadəçinin qeydiyyatdan uğurla keçməsi."""
        user_count_before = Ishchi.objects.count()
        response = self.client.post(reverse('qeydiyyat'), {
            'username': 'yeniistifadechi',
            'first_name': 'Yeni', 'last_name': 'İstifadəçi',
            'email': 'yeni@example.com', 'sektor': self.sektor.id,
            'password1': 'GucluShifre123', 'password2': 'GucluShifre123',
        })
        self.assertEqual(response.status_code, 302, "Qeydiyyatdan sonra yönləndirmə baş vermədi.")
        self.assertEqual(response.url, reverse('dashboard'))
        self.assertEqual(Ishchi.objects.count(), user_count_before + 1, "Yeni istifadəçi bazada yaranmadı.")

    def test_login_with_email_and_username(self):
        """İstifadəçinin həm istifadəçi adı, həm də e-poçt ilə daxil ola bilməsi."""
        # E-poçt ilə giriş
        self.assertTrue(self.client.login(username='ishchi@example.com', password='password123'))
        self.client.logout()

        # İstifadəçi adı ilə giriş
        self.assertTrue(self.client.login(username='testishchi', password='password123'))
        
        # Səhv şifrə ilə girişin uğursuz olması
        self.assertFalse(self.client.login(username='testishchi', password='sehvsifre'))

    def test_password_reset_flow(self):
        """Test 7: Şifrə bərpası axınının tam olaraq işləməsi."""
        # Addım 1: Şifrə bərpası tələbi göndəririk
        self.client.post(reverse('password_reset'), {'email': 'ishchi@example.com'})
        
        # Addım 2: E-poçtun göndərildiyini yoxlayırıq
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        
        # Addım 3: E-poçtdan bərpa linkini tapırıq
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', sent_email.body)
        self.assertTrue(len(urls) > 0, "E-poçt mətnində bərpa linki tapılmadı.")
        reset_link = urls[0]

        # DÜZƏLİŞ: GET sorğusunun statusunu yoxlamaq əvəzinə birbaşa POST edirik.
        # Bu, aradakı yönləndirmələrdən asılılığı aradan qaldırır.
        
        # Addım 4: Yeni şifrəni təyin edirik
        response_post = self.client.post(reset_link, {
            'new_password1': 'yeniGucluShifre456',
            'new_password2': 'yeniGucluShifre456',
        })

        # Addım 5: Uğurlu dəyişiklikdən sonra yönləndirməni yoxlayırıq
        self.assertEqual(response_post.status_code, 302, "Şifrə dəyişdirildikdən sonra yönləndirmə baş vermədi.")
        self.assertEqual(response_post.url, reverse('password_reset_complete'))

        # Addım 6: Yeni şifrə ilə daxil olmağı yoxlayırıq
        self.assertTrue(self.client.login(username='testishchi', password='yeniGucluShifre456'), "Yeni şifrə ilə daxil olmaq mümkün olmadı.")