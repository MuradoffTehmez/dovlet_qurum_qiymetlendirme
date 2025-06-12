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
    def test_dashboard_redirect_for_unauthenticated(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(settings.LOGIN_URL, resp.url)

    def test_dashboard_access_authenticated(self):
        self.client.login(username='testishchi', password='password123')
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Qiymətləndirmə Tapşırıqlarınız")

    def test_superadmin_panel_permission(self):
        self.client.login(username='testishchi', password='password123')
        resp = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(resp.status_code, 403)

        self.client.login(username='testsuperadmin', password='password123')
        resp = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(resp.status_code, 200)


class AuthenticationFlowTests(BaseTestCase):
    def test_registration_flow(self):
        count = Ishchi.objects.count()
        resp = self.client.post(reverse('qeydiyyat'), {
            'username': 'yeniuser',
            'first_name': 'Yeni', 'last_name': 'İstifadəçi',
            'email': 'yeni@example.com', 'sektor': self.sektor.id,
            'password1': 'Str0ngPass!23', 'password2': 'Str0ngPass!23',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Ishchi.objects.count(), count + 1)
        self.assertEqual(resp.url, reverse('dashboard'))

    def test_login_with_username_and_email(self):
        self.assertTrue(self.client.login(username='ishchi@example.com', password='password123'))
        self.client.logout()
        self.assertTrue(self.client.login(username='testishchi', password='password123'))
        self.assertFalse(self.client.login(username='testishchi', password='wrongpass'))

    def test_password_reset_process(self):
        self.client.post(reverse('password_reset'), {'email': 'ishchi@example.com'})
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        links = re.findall(r'https?://\\S+', body)
        self.assertGreater(len(links), 0)
        link = links[0]

        resp_get = self.client.get(link)
        self.assertEqual(resp_get.status_code, 200)

        resp_post = self.client.post(link, {
            'new_password1': 'Yen1Guclu!', 'new_password2': 'Yen1Guclu!'
        })
        self.assertEqual(resp_post.status_code, 302)
        self.assertEqual(resp_post.url, reverse('password_reset_complete'))
        self.assertTrue(self.client.login(username='testishchi', password='Yen1Guclu!'))


class RolePermissionTests(BaseTestCase):
    def test_role_switch(self):
        self.assertEqual(self.normal_user.rol, 'ISHCHI')
        self.normal_user.rol = 'REHBER'
        self.normal_user.save()
        usr = Ishchi.objects.get(pk=self.normal_user.pk)
        self.assertEqual(usr.rol, 'REHBER')

    def test_manager_cant_access_superadmin(self):
        self.client.login(username='testrehber', password='password123')
        resp = self.client.get(reverse('superadmin_paneli'))
        self.assertEqual(resp.status_code, 403)


class ModelRelationshipTests(BaseTestCase):
    def test_create_review_cycle_and_development(self):
        self.client.login(username='testsuperadmin', password='password123')
        ciklus = QiymetlendirmeDovru.objects.create(ad="2025 Yarımdönəm", sektor=self.sektor)
        plan = InkishafPlani.objects.create(user=self.normal_user, dovru=ciklus)
        hedef = Hedef.objects.create(plan=plan, ad="Məqsəd 1", təsvir="Təsvir")
        self.assertEqual(hedef.plan, plan)
        self.assertEqual(plan.user, self.normal_user)


class ValidationErrorTests(BaseTestCase):
    def test_weak_password_registration(self):
        resp = self.client.post(reverse('qeydiyyat'), {
            'username': 'weak',
            'first_name': 'Zəif', 'last_name': 'Şifrə',
            'email': 'weak@example.com', 'sektor': self.sektor.id,
            'password1': '123', 'password2': '123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bu şifrə çox qısadır")

    def test_duplicate_email_error(self):
        resp = self.client.post(reverse('qeydiyyat'), {
            'username': 'dupuser',
            'first_name': 'Eyni', 'last_name': 'E-poçt',
            'email': 'ishchi@example.com', 'sektor': self.sektor.id,
            'password1': 'Str0ngPass!23', 'password2': 'Str0ngPass!23',
        })
        self.assertContains(resp, "Bu e-poçt artıq istifadə olunur")


class UIElementsTests(BaseTestCase):
    def test_login_page_text(self):
        resp = self.client.get(reverse('login'))
        self.assertContains(resp, "Daxil ol")
        self.assertContains(resp, "İstifadəçi adı və ya e-poçt")

    def test_registration_page_text(self):
        resp = self.client.get(reverse('qeydiyyat'))
        self.assertContains(resp, "Qeydiyyat")
        self.assertContains(resp, "Şifrəni təsdiqlə")
