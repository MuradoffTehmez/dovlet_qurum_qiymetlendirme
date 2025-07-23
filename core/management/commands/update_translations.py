"""
Management command to update translation files
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import subprocess


class Command(BaseCommand):
    help = 'Update translation files for all languages'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            help='Update specific language only'
        )
        parser.add_argument(
            '--compile',
            action='store_true',
            help='Compile messages after updating'
        )
        parser.add_argument(
            '--check-missing',
            action='store_true',
            help='Check for missing translations'
        )
    
    def handle(self, *args, **options):
        language = options.get('language')
        compile_messages = options.get('compile', False)
        check_missing = options.get('check_missing', False)
        
        if language:
            languages = [language]
        else:
            languages = [code for code, name in settings.LANGUAGES]
        
        self.stdout.write(
            self.style.SUCCESS(f'Updating translations for: {", ".join(languages)}')
        )
        
        # Extract messages
        self.stdout.write('Extracting translatable strings...')
        try:
            call_command('makemessages', 
                        locale=languages, 
                        ignore_patterns=['venv/*', 'node_modules/*'],
                        verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Messages extracted'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error extracting messages: {e}'))
            return
        
        # Check for missing translations
        if check_missing:
            self.check_missing_translations(languages)
        
        # Compile messages
        if compile_messages:
            self.stdout.write('Compiling messages...')
            try:
                call_command('compilemessages', verbosity=1)
                self.stdout.write(self.style.SUCCESS('✓ Messages compiled'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error compiling messages: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS('Translation update completed!')
        )
    
    def check_missing_translations(self, languages):
        """Check for missing translations"""
        from core.i18n_utils import translation_manager
        
        self.stdout.write('Checking for missing translations...')
        
        for lang_code in languages:
            if lang_code == settings.LANGUAGE_CODE:
                continue  # Skip default language
            
            missing = translation_manager.get_missing_translations(lang_code)
            
            if missing:
                self.stdout.write(
                    self.style.WARNING(f'⚠ {lang_code}: {len(missing)} missing translations')
                )
                for i, msg in enumerate(missing[:5]):  # Show first 5
                    self.stdout.write(f'  - {msg}')
                if len(missing) > 5:
                    self.stdout.write(f'  ... and {len(missing) - 5} more')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {lang_code}: All translations complete')
                )