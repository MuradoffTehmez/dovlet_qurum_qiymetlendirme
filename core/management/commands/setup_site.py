from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Set up the site domain for email links'

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            type=str,
            help='The domain name for your site (e.g., www.yoursite.az)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='My Site',
            help='The display name for your site'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        name = options['name']
        
        # Update or create the site
        site, created = Site.objects.get_or_create(id=1)
        site.domain = domain
        site.name = name
        site.save()
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created site: {name} ({domain})')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated site: {name} ({domain})')
            )
        
        self.stdout.write(
            self.style.WARNING(
                'Remember to update ALLOWED_HOSTS in settings.py with your domain!'
            )
        )