#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()


import os
import subprocess
from django.core.management.base import BaseCommand

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class Color:
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    RESET = '\033[0m'
    HEADER = '\033[96m'

class Command(BaseCommand):
    help = "Layihənin bütün Python və Django kodlarını analiz edir (Prettier stilində)"

    def handle(self, *args, **options):
        self.stdout.write(f"{Color.HEADER}🚀 Django Kod Audit Başladı (Prettier Stilində){Color.RESET}\n")

        self.run_command("PEP8 və sintaksis yoxlaması (flake8)", ["flake8", BASE_DIR])
        self.run_command("Kod keyfiyyəti (pylint)", ["pylint", BASE_DIR])
        self.run_command("Tip yoxlaması (mypy)", ["mypy", BASE_DIR])
        self.run_command("Təhlükəsizlik analizləri (bandit)", ["bandit", "-r", BASE_DIR])
        self.run_django_checks()

        self.stdout.write(f"\n{Color.OK}✅ Audit tamamlandı.{Color.RESET}")

    def run_command(self, title, command):
        self.stdout.write(f"{Color.HEADER}▶ {title}{Color.RESET}")
        if not shutil.which(command[0]):
            self.stdout.write(f"{Color.WARNING}⚠ Alət tapılmadı: {command[0]}{Color.RESET}")
            return
        result = subprocess.run(command, capture_output=True, text=True)
        if result.stdout.strip():
            self.stdout.write(f"{Color.OK}✔ Çıxış:\n{result.stdout}{Color.RESET}")
        if result.stderr.strip():
            self.stdout.write(f"{Color.ERROR}✘ Xəta:\n{result.stderr}{Color.RESET}")
        if not result.stdout.strip() and not result.stderr.strip():
            self.stdout.write(f"{Color.OK}✔ Heç bir problem tapılmadı.{Color.RESET}")
        self.stdout.write("-" * 70)

    def run_django_checks(self):
        from django.core import checks
        try:
            errors = checks.run_checks()
            self.stdout.write(f"{Color.HEADER}▶ Django Check Analizi{Color.RESET}")
            if not errors:
                self.stdout.write(f"{Color.OK}✔ Django konfiqurasiyası düzgündür.{Color.RESET}")
            else:
                for e in errors:
                    level = e.level_tag.upper()
                    color = {
                        'ERROR': Color.ERROR,
                        'WARNING': Color.WARNING,
                        'INFO': Color.HEADER,
                    }.get(level, Color.RESET)
                    self.stdout.write(f"{color}❗ {level}: {e.msg}{Color.RESET}")
                    if e.hint:
                        self.stdout.write(f"   💡 İpucu: {e.hint}")
                    if e.obj:
                        self.stdout.write(f"   📍 Obyekt: {e.obj}")
        except Exception as e:
            self.stdout.write(f"{Color.ERROR}✘ Django yoxlamasında xəta: {e}{Color.RESET}")
        self.stdout.write("-" * 70)
