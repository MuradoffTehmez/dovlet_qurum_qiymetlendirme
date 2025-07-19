# core/tests/test_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from core.models import (
    OrganizationUnit, Ishchi, SualKateqoriyasi, Sual,
    QiymetlendirmeDovru, Qiymetlendirme, InkishafPlani,
    Feedback, Notification, CalendarEvent
)

User = get_user_model()


class OrganizationUnitModelTest(TestCase):
    def setUp(self):
        self.parent_unit = OrganizationUnit.objects.create(
            name="Ana Şirkət",
            type=OrganizationUnit.UnitType.ALI_IDARE
        )
        self.child_unit = OrganizationUnit.objects.create(
            name="İT Departamenti",
            type=OrganizationUnit.UnitType.SHOBE,
            parent=self.parent_unit
        )

    def test_organization_unit_creation(self):
        """Təşkilati vahid yaradılmasını test et"""
        self.assertEqual(self.parent_unit.name, "Ana Şirkət")
        self.assertEqual(self.child_unit.parent, self.parent_unit)

    def test_get_full_path(self):
        """Hierarchik yol metodunu test et"""
        expected_path = "Ana Şirkət → İT Departamenti"
        self.assertEqual(self.child_unit.get_full_path(), expected_path)

    def test_get_children_count(self):
        """Alt vahidlərin sayını test et"""
        self.assertEqual(self.parent_unit.get_children_count(), 1)
        self.assertEqual(self.child_unit.get_children_count(), 0)


class IshchiModelTest(TestCase):
    def setUp(self):
        self.org_unit = OrganizationUnit.objects.create(
            name="Test Departament",
            type=OrganizationUnit.UnitType.SHOBE
        )
        
        self.user = Ishchi.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            rol=Ishchi.Rol.ISHCHI,
            vezife="Test Mütəxəssisi",
            organization_unit=self.org_unit
        )

    def test_user_creation(self):
        """İstifadəçi yaradılmasını test et"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.rol, Ishchi.Rol.ISHCHI)
        self.assertEqual(self.user.organization_unit, self.org_unit)

    def test_user_str_method(self):
        """İstifadəçi string metodunu test et"""
        expected = "Test User"
        self.assertEqual(str(self.user), expected)


class QiymetlendirmeDovruModelTest(TestCase):
    def test_evaluation_cycle_creation(self):
        """Qiymətləndirmə dövrü yaradılmasını test et"""
        dovr = QiymetlendirmeDovru.objects.create(
            ad="2025 Q1 Qiymətləndirməsi",
            bashlama_tarixi=date.today(),
            bitme_tarixi=date.today() + timedelta(days=30),
            aktivdir=True,
            anonymity_level=QiymetlendirmeDovru.AnonymityLevel.MANAGER_ONLY
        )
        
        self.assertEqual(dovr.ad, "2025 Q1 Qiymətləndirməsi")
        self.assertTrue(dovr.aktivdir)

    def test_anonymity_check(self):
        """Anonimlik yoxlamasını test et"""
        dovr = QiymetlendirmeDovru.objects.create(
            ad="Test Dövrü",
            bashlama_tarixi=date.today(),
            bitme_tarixi=date.today() + timedelta(days=30),
            anonymity_level=QiymetlendirmeDovru.AnonymityLevel.FULL_ANONYMOUS
        )
        
        user = Ishchi.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123",
            rol=Ishchi.Rol.ISHCHI
        )
        
        self.assertTrue(dovr.is_anonymous_for_user(user))


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = Ishchi.objects.create_user(
            username="testuser3",
            email="test3@example.com",
            password="testpass123"
        )

    def test_notification_creation(self):
        """Bildiriş yaradılmasını test et"""
        notification = Notification.objects.create(
            recipient=self.user,
            title="Test Bildirişi",
            message="Bu bir test bildirişidir.",
            notification_type=Notification.NotificationType.INFO
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, "Test Bildirişi")
        self.assertFalse(notification.is_read)

    def test_notification_str_method(self):
        """Bildiriş string metodunu test et"""
        notification = Notification.objects.create(
            recipient=self.user,
            title="Test Bildirişi",
            message="Test mesajı"
        )
        
        expected = f"{self.user.username} - Test Bildirişi"
        self.assertEqual(str(notification), expected)


class InkishafPlaniModelTest(TestCase):
    def setUp(self):
        self.user = Ishchi.objects.create_user(
            username="testuser4",
            email="test4@example.com",
            password="testpass123"
        )
        
        self.dovr = QiymetlendirmeDovru.objects.create(
            ad="Test Dövrü",
            bashlama_tarixi=date.today(),
            bitme_tarixi=date.today() + timedelta(days=30)
        )

    def test_development_plan_creation(self):
        """İnkişaf planı yaradılmasını test et"""
        plan = InkishafPlani.objects.create(
            ishchi=self.user,
            dovr=self.dovr
        )
        
        self.assertEqual(plan.ishchi, self.user)
        self.assertEqual(plan.dovr, self.dovr)
        self.assertEqual(plan.status, InkishafPlani.Status.AKTIV)

    def test_development_plan_unique_constraint(self):
        """İnkişaf planının unikal məhdudiyyətini test et"""
        InkishafPlani.objects.create(
            ishchi=self.user,
            dovr=self.dovr
        )
        
        # Eyni istifadəçi və dövr üçün ikinci plan yaratmaq xəta verməlidir
        with self.assertRaises(Exception):
            InkishafPlani.objects.create(
                ishchi=self.user,
                dovr=self.dovr
            )