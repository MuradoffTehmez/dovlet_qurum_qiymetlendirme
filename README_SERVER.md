# Q360 Performance Management System

## 🚀 Server Başlatma

### Windows istifadəçiləri üçün:

#### Method 1: Batch Script (Sadə)
```cmd
run_server.bat
```

#### Method 2: PowerShell Script (Təfərrüatlı)
```powershell
.\run_server.ps1
```

#### Method 3: Manual (Əl ilə)
```cmd
# 1. Virtual environment activate et
venv\Scripts\activate

# 2. Dependencies yoxla/quraşdır  
pip install -r requirements.txt

# 3. Server başlat
python manage.py runserver 127.0.0.1:8000
```

### Linux/Mac istifadəçiləri üçün:
```bash
# 1. Virtual environment activate et
source venv/bin/activate

# 2. Dependencies quraşdır
pip install -r requirements.txt

# 3. Server başlat
python manage.py runserver 127.0.0.1:8000
```

## 🌐 Giriş URL-ləri

Ana server başladıqdan sonra browser-də açın:

- **Ana Səhifə**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **İnteraktiv Dashboard**: http://127.0.0.1:8000/interactive-dashboard/
- **Təqvim**: http://127.0.0.1:8000/teqvim/
- **Bildirişlər**: http://127.0.0.1:8000/bildirisler/
- **Hesabatlar**: http://127.0.0.1:8000/hesabatlar/

## 📋 Əsas Modullar

### ✅ Tamamlanmış Features:
1. **Notification System** - Real-time bildiriş mərkəzi
2. **Reporting Hub** - PDF/Excel/CSV hesabat generasiyası  
3. **Calendar Module** - FullCalendar.js ilə interaktiv təqvim
4. **Interactive Dashboard** - Chart.js ilə analytics
5. **Modern UI/UX** - Bootstrap 5 və responsive design
6. **RBAC System** - Role-based access control
7. **Audit Logging** - Comprehensive activity tracking
8. **Cache Optimization** - Redis-based performance

### 🔧 Technical Stack:
- **Backend**: Django 5.2.3
- **Frontend**: Bootstrap 5, Chart.js, FullCalendar.js
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Cache**: Redis
- **Task Queue**: Celery
- **PDF Generation**: ReportLab
- **Authentication**: Django Auth + Custom

## 🛠️ Troubleshooting

### Problem: ImportError reportlab
```cmd
pip install reportlab
```

### Problem: Virtual Environment
```cmd
# Windows
venv\Scripts\activate

# Linux/Mac  
source venv/bin/activate
```

### Problem: Port məşğul
```cmd
# Başqa port istifadə edin
python manage.py runserver 127.0.0.1:8001
```

### Problem: Database
```cmd
# Migration-ları run edin
python manage.py migrate
```

## 📝 Development

### Test üçün:
```cmd
python manage.py test
```

### Superuser yaratmaq:
```cmd
python manage.py createsuperuser
```

### Dependencies yeniləmək:
```cmd
pip install -r requirements.txt
```

## 🔒 Production Deployment

Production üçün aşağıdakı settings-ləri dəyişin:
- `DEBUG = False`
- `ALLOWED_HOSTS` təyin edin
- PostgreSQL/MySQL istifadə edin  
- HTTPS konfiqurə edin
- Static files nginx ilə serve edin

---

**🎉 Q360 Performance Management System - Ready to Use! 🎉**