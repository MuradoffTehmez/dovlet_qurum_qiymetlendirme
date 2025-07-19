# core/management/commands/create_default_surveys.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.psychological_surveys import PsychologicalSurveyManager

User = get_user_model()


class Command(BaseCommand):
    help = 'Standart psixoloji risk sorğularını yaradır'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Sorğuları yaradan admin istifadəçinin adı'
        )
    
    def handle(self, *args, **options):
        admin_username = options['admin_username']
        
        try:
            admin_user = User.objects.get(username=admin_username, rol='SUPERADMIN')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Admin istifadəçi tapılmadı: {admin_username}')
            )
            return
        
        manager = PsychologicalSurveyManager()
        surveys = manager.create_default_surveys(admin_user)
        
        if surveys:
            self.stdout.write(
                self.style.SUCCESS(f'{len(surveys)} yeni sorğu yaradıldı:')
            )
            for survey in surveys:
                self.stdout.write(f'  - {survey.title} ({survey.survey_type})')
        else:
            self.stdout.write(
                self.style.WARNING('Bütün standart sorğular artıq mövcuddur')
            )