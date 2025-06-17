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

# Layihənin kök qovluğu
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def run_command(description, command):
    print(f"\n🔍 {description}")
    print(f"📎 Komanda: {' '.join(command)}\n")
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("⚠️  Xəta/Məlumat:", result.stderr)

def main():
    print("📦 Django Layihə Kod Auditi Başladı...\n")

    # Kod analizləri
    run_command("PEP8 və sintaksis yoxlaması (flake8)", ["flake8", BASE_DIR])
    run_command("Kod keyfiyyəti yoxlaması (pylint)", ["pylint", BASE_DIR])
    run_command("Statik təhlükəsizlik yoxlaması (bandit)", ["bandit", "-r", BASE_DIR])
    run_command("Tip yoxlaması (mypy)", ["mypy", BASE_DIR])

    # Django checks
    print("\n🧪 Django daxili 'checks' yoxlaması:")
    try:
        import django
        from django.core import checks
        django.setup()
        errors = checks.run_checks()
        if not errors:
            print("✅ Django sistemində heç bir problem aşkar edilmədi.")
        else:
            for e in errors:
                print(f"❌ {e.msg} | Level: {e.level_tag}")
    except Exception as e:
        print(f"❗ Django yoxlamasında xəta: {e}")

    print("\n✅ Audit tamamlandı.")

if __name__ == "__main__":
    main()
