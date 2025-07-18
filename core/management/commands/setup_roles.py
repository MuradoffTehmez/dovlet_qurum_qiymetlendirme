# core/management/commands/setup_roles.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.permissions import ROLE_PERMISSIONS, create_role_groups

class Command(BaseCommand):
    help = 'Q360 layihəsi üçün rolları və icazələri qurur'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Rolların qurulması başladı...'))
        
        try:
            create_role_groups()
            self.stdout.write(
                self.style.SUCCESS('✅ Bütün rollar və icazələr uğurla yaradıldı!')
            )
            
            # Yaradılan rolları göstər
            self.stdout.write('\n📋 Yaradılan rollar:')
            for role_name in ROLE_PERMISSIONS.keys():
                group = Group.objects.get(name=role_name)
                perm_count = group.permissions.count()
                self.stdout.write(f'  • {role_name}: {perm_count} icazə')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Xəta baş verdi: {e}')
            )