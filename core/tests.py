# core/tests.py - GENİŞLƏNDİRİLMİŞ TEST DƏSTİ

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from .models import (
    Ishchi, Sektor, Shobe, Departament, 
    QiymetlendirmeDovru, InkishafPlani, Hedef
)

# Testləri qruplaşdırmaq üçün ümumi bir "hazırlıq" sinfi yaradırıq
class BaseTestCase(TestCase):
    def setUp(self):
        """Bütün test sinifləri üçün ortaq olan hazırlıq."""
        self.client = Client()
        self.departament = Departament.objects.create(ad="Test Departamenti")
        self.shobe = Shobe.objects.create(ad="Test Şöbəsi", departament=self.departament)
        self.sektor = Sektor.objects.create(ad="Test Sektoru", shobe=self.shobe)

        self.normal_user = Ishchi.objects.create_user(
            username='testishchi', password='password123', rol='ISHCHI', 
            sektor=self.sektor, first_name="Test", last_name="İşçi"
        )
        self.manager_user = Ishchi.objects.create_user(
            username='testrehber', password='password123', rol='REHBER', 
            sektor=self.sektor, first_name="Test", last_name="Rəhbər"
        )
        self.superadmin_user = Ishchi.objects.create_user(
            username='testsuperadmin', password='password123', rol='SUPERADMIN', 
            sektor=self.sektor, is_staff=True, is_superuser=True
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

# --- Test Sinif 2: Fərdi İnkişaf Planı (IDP) Axını ---
class IDPWorkflowTests(BaseTestCase):

    def setUp(self):
        """Bu test sinfi üçün əlavə hazırlıq."""
        super().setUp() # Əsas BaseTestCase-in hazırlığını çağırırıq
        self.dovr = QiymetlendirmeDovru.objects.create(
            ad="Test IDP Dövrü", 
            bashlama_tarixi="2025-01-01", 
            bitme_tarixi="2025-12-31"
        )

    def test_manager_can_create_idp(self):
        """Test 5: Rəhbərin işçi üçün yeni bir IDP yarada bilməsi."""
        self.client.login(username='testrehber', password='password123')
        
        # Plan yaratma səhifəsinə POST sorğusu göndəririk
        url = reverse('plan_yarat', kwargs={'ishchi_id': self.normal_user.id, 'dovr_id': self.dovr.id})
        post_data = {
            'hedefler-TOTAL_FORMS': '1',
            'hedefler-INITIAL_FORMS': '0',
            'hedefler-MIN_NUM_FORMS': '1',
            'hedefler-MAX_NUM_FORMS': '1000',
            'hedefler-0-tesvir': 'Yeni bir bacarıq öyrənmək',
            'hedefler-0-son_tarix': '2025-10-10',
            'hedefler-0-status': 'BASHLANMAYIB',
        }
        response = self.client.post(url, data=post_data)
        
        # Gözləyirik ki, uğurlu əməliyyatdan sonra yönləndirmə olsun (302)
        self.assertEqual(response.status_code, 302)
        
        # Verilənlər bazasında planın və hədəfin yarandığını yoxlayırıq
        self.assertTrue(InkishafPlani.objects.filter(ishchi=self.normal_user, dovr=self.dovr).exists())
        self.assertTrue(Hedef.objects.filter(plan__ishchi=self.normal_user, tesvir='Yeni bir bacarıq öyrənmək').exists())

    def test_employee_can_update_goal_status(self):
        """Test 6: İşçinin öz IDP hədəfinin statusunu yeniləyə bilməsi."""
        # Əvvəlcə rəhbər tərəfindən bir plan və hədəf yaradırıq
        plan = InkishafPlani.objects.create(ishchi=self.normal_user, dovr=self.dovr)
        hedef = Hedef.objects.create(plan=plan, tesvir='Test hədəfi', son_tarix='2025-09-01', status='BASHLANMAYIB')
        
        # İndi işçi kimi daxil oluruq
        self.client.login(username='testishchi', password='password123')
        
        # Plana baxış səhifəsinə POST sorğusu göndərərək statusu dəyişirik
        url = reverse('plan_bax', kwargs={'plan_id': plan.id})
        post_data = {
            'hedef_id': hedef.id,
            'status': 'DAVAM_EDIR',
        }
        self.client.post(url, data=post_data)
        
        # Hədəfin statusunun bazada dəyişdiyini yoxlayırıq
        hedef.refresh_from_db()
        self.assertEqual(hedef.status, 'DAVAM_EDIR')