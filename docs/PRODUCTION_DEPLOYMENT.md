# Production Deployment Guide

This document outlines the critical steps needed to deploy this Django application to production after applying the bug fixes.

## 1. Site Configuration (Required for Email Links)

After deployment, you must configure the site domain to ensure email activation links and notifications work correctly:

```bash
# Replace 'www.yoursite.az' with your actual domain
python manage.py setup_site www.yoursite.az --name "Your Site Name"
```

## 2. ALLOWED_HOSTS Configuration

Update `config/settings.py` to include only your actual domain names:

```python
ALLOWED_HOSTS = [
    "www.yoursite.az",
    "api.yoursite.az", 
    "yoursite.az"
]
```

**Never use "*" in production - it's a security vulnerability!**

## 3. Database Migrations

If you haven't already applied the email uniqueness constraint:

```bash
python manage.py makemigrations core --name add_unique_email_constraint
python manage.py migrate
```

## 4. Sites Framework Migration

Ensure the Sites framework is properly set up:

```bash
python manage.py migrate sites
```

## 5. SSL Configuration

For HTTPS sites, ensure these settings are configured:

```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TLS = True
```

## 6. Email Backend Configuration

Configure your email settings in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@yoursite.az'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'your-email@yoursite.az'
```

## 7. Performance Monitoring

The following performance issues have been fixed:
- ✅ PDF Report Template corrected
- ✅ N+1 query issues in participation monitoring resolved
- ✅ N+1 query issues in gap analysis resolved  
- ✅ N+1 query issues in performance trends resolved
- ✅ Email activation links now use dynamic domain names
- ✅ ALLOWED_HOSTS security vulnerability fixed

## 8. Testing Checklist

Before going live, test these features:

- [ ] User registration and email activation
- [ ] Performance evaluation assignment notifications
- [ ] PDF report generation for departments
- [ ] Participation monitoring dashboard loads quickly
- [ ] Gap analysis pages load quickly
- [ ] Performance trends pages load quickly
- [ ] All email links point to correct domain

## 9. Cleanup Duplicate Emails (if any)

If you have existing duplicate emails in your database, run this before migrating:

```python
# In Django shell: python manage.py shell
from core.models import Ishchi
from django.db.models import Count

# Find duplicates
duplicates = Ishchi.objects.values('email').annotate(
    count=Count('email')
).filter(count__gt=1).exclude(email='')

# Review and manually resolve duplicates before applying migration
```

## Notes

- The application now uses Django's Sites framework for dynamic URL generation
- All database queries have been optimized to eliminate N+1 query problems
- Security vulnerabilities in ALLOWED_HOSTS have been addressed
- Email activation system now works properly with correct token generation