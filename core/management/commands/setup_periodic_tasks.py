"""
Django management command to setup periodic Celery Beat tasks
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Q360 üçün perodik tapşırıqları qurur'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Perodik tapşırıqlar qurulur...'))
        
        # Avtomatik dövr yaratma - hər ayın 1-də
        self.setup_automatic_cycle_creation()
        
        # Son tarix xatırlatmaları - hər gün
        self.setup_deadline_reminders()
        
        # Bildiriş təmizləmə - həftəlik
        self.setup_notification_cleanup()
        
        # AI Risk Detection - gündəlik
        self.setup_ai_risk_detection()
        
        # Psixoloji risk analizi - gündəlik
        self.setup_psychological_risk_analysis()
        
        # Standart psixoloji sorğuları yaratma - həftəlik
        self.setup_default_psychological_surveys()
        
        self.stdout.write(self.style.SUCCESS('Bütün perodik tapşırıqlar uğurla quruldu!'))

    def setup_automatic_cycle_creation(self):
        """Avtomatik qiymətləndirmə dövrü yaratma"""
        # Crontab: Hər ayın 1-də saat 09:00-da
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=9,
            day_of_month=1,
            month_of_year='*',
            day_of_week='*'
        )
        
        task, created = PeriodicTask.objects.get_or_create(
            name='Avtomatik Qiymətləndirmə Dövrü Yaratma',
            defaults={
                'crontab': schedule,
                'task': 'core.tasks.create_automatic_evaluation_cycle',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Avtomatik dövr yaratma tapşırığı quruldu')
        else:
            self.stdout.write(f'✓ Avtomatik dövr yaratma tapşırığı artıq mövcuddur')

    def setup_deadline_reminders(self):
        """Son tarix xatırlatmaları"""
        # Crontab: Hər gün saat 10:00-da
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=10,
            day_of_month='*',
            month_of_year='*',
            day_of_week='*'
        )
        
        task, created = PeriodicTask.objects.get_or_create(
            name='Qiymətləndirmə Son Tarix Xatırlatmaları',
            defaults={
                'crontab': schedule,
                'task': 'core.tasks.send_evaluation_deadline_reminders',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Son tarix xatırlatma tapşırığı quruldu')
        else:
            self.stdout.write(f'✓ Son tarix xatırlatma tapşırığı artıq mövcuddur')

    def setup_notification_cleanup(self):
        """Bildiriş təmizləmə"""
        # Crontab: Hər bazar ertəsi saat 02:00-da
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_month='*',
            month_of_year='*',
            day_of_week=1  # Monday
        )
        
        task, created = PeriodicTask.objects.get_or_create(
            name='Köhnə Bildiriş Təmizləmə',
            defaults={
                'crontab': schedule,
                'task': 'core.tasks.cleanup_old_notifications',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Bildiriş təmizləmə tapşırığı quruldu')
        else:
            self.stdout.write(f'✓ Bildiriş təmizləmə tapşırığı artıq mövcuddur')

    def setup_ai_risk_detection(self):
        """AI Risk Detection gündəlik analizi"""
        # Crontab: Hər gün saat 08:00-da
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=8,
            day_of_month='*',
            month_of_year='*',
            day_of_week='*'
        )
        
        task, created = PeriodicTask.objects.get_or_create(
            name='AI Risk Detection Gündəlik Analizi',
            defaults={
                'crontab': schedule,
                'task': 'core.tasks.run_ai_risk_detection',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ AI Risk Detection tapşırığı quruldu')
        else:
            self.stdout.write(f'✓ AI Risk Detection tapşırığı artıq mövcuddur')

    def setup_psychological_risk_analysis(self):
        """Psixoloji risk analizi gündəlik"""
        # Crontab: Hər gün saat 09:30-da
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=30,
            hour=9,
            day_of_month='*',
            month_of_year='*',
            day_of_week='*'
        )
        
        task, created = PeriodicTask.objects.get_or_create(
            name='Psixoloji Risk Analizi',
            defaults={
                'crontab': schedule,
                'task': 'core.tasks.run_psychological_risk_analysis',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Psixoloji risk analizi tapşırığı quruldu')
        else:
            self.stdout.write(f'✓ Psixoloji risk analizi tapşırığı artıq mövcuddur')

    def setup_default_psychological_surveys(self):
        """Standart psixoloji sorğuları yaratma"""
        # Crontab: Hər çərşənbə axşamı saat 23:00-da
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=23,
            day_of_month='*',
            month_of_year='*',
            day_of_week=3  # Wednesday
        )
        
        task, created = PeriodicTask.objects.get_or_create(
            name='Standart Psixoloji Sorğuları Yaratma',
            defaults={
                'crontab': schedule,
                'task': 'core.tasks.create_default_psychological_surveys',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Standart psixoloji sorğuları tapşırığı quruldu')
        else:
            self.stdout.write(f'✓ Standart psixoloji sorğuları tapşırığı artıq mövcuddur')