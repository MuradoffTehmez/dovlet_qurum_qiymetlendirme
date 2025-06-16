# 360 Dərəcə Qiymətləndirmə Sistemi

# 360 Degree Appraisal System

**360 Dərəcə Qiymətləndirmə Sistemi** – dövlət idarələri, ictimai qurumlar və ya özəl sektor təşkilatları ücün işçilərin kompetensiyaları üzrə obyektiv qiymətləndirilməsini təmin edən, Django framework-u ilə yaradılmış tam funksional və müsasir veb-platformadır. Sistem, istinad edilən beynəlxalq qiymətləndirmə standartlarını əsas götürərək istənilən strukturda səmərəli performans idarəetməsini mümkün edir.

**360 Degree Appraisal System**  is a fully functional and modern web platform built with the Django framework, which provides objective assessment of employees' competencies for government agencies, public institutions or private sector organizations. The system enables effective performance management in any structure, based on referenced international assessment standards.

---

## ƏSAS FUNKSİONALLIQ

## Core Functionality

### ✔️ Rol əsaslı idarəetmə

### ✔️ Role-Based Management

* **Superadmin**: Sistemin tam idarəetməsini aparır, qiymətləndirmə dövrlərini yaradar, orqanları idarə edər.
  **Superadmin**: Has full control of the system, creates evaluation periods, and manages institutions.
* **Admin**: Qurum daxilində struktur, işçi qeydiyyatı və hesabatlara baxış.
  **Admin**: Manages internal structures, employee registration, and views reports.
* **Rəhbər**: Öz strukturundaki işçiləri qiymətləndirir və hesabat alır.
  **Manager**: Evaluates subordinates and receives performance reports.
* **Işçi**: Özünü, rəhbəri və komanda yoldaşlarını qiymətləndirir.
  **Employee**: Evaluates self, supervisor, and team members.

### ✔️ Dinamik Qiymətləndirmə Modulu

(Dynamic Evaluation Module)

* Superadmin tərəfindən qiymətləndirmə kampaniyaları yaradılır.
  (Evaluation campaigns are created by the Superadmin.)
* Avtomatik algoritm vasitəsilə qiymətləndirici qruplar təyin edilir (360º model: özü, rəhbər, eyni səviyyə).
  (Evaluator groups are assigned using an automatic algorithm (360º model: self, supervisor, peer).)
* Kompetensiyalar və meyarlar ixtiyarə verilən parametrlərə görə formalaşdırılır.
  (Competencies and criteria are defined based on configurable parameters.)

### ✔️ Hesabatlar və Analitika

(Reports and Analytics)

* **Radar Chart**: Kompetensiya paylanması.
  (Radar Chart: Competency distribution.)
* **Line Chart**: Vaxt üzrə performans dəyişiklikləri.
  (Line Chart: Performance changes over time.)
* Şəxsi, struktur və ümumi hesabatlar PDF/Excel formatlarında.
  (Individual, departmental, and overall reports available in PDF/Excel formats.)

### ✔️ UX/UI Dizayn və Multidillilik

### ✔️ UX/UI Design and Multilingual Support

* `django-jazzmin` temasi ilə admin paneli tam yenidən dizayn olunub.
  (Admin panel redesigned with `django-jazzmin` theme.)
* Bootstrap 5, `crispy-bootstrap5` ilə responsiv formalar.
  (Responsive forms powered by Bootstrap 5 and `crispy-bootstrap5`.)
* Dark/Light rejim dəstəyi.
  (Supports Dark/Light mode.)
* Daxili çevirmə modulu (gettext .po/.mo faylları).
  (Built-in translation engine with gettext support.)

### ✔️ Digər Funksiyalar

### (Other Features)

* **Audit Trail (Tarixçə):** Hər bir əməliyyat qeydi saxlanılır.
  (Audit Trail: Logs every user action and system event.)
* **Fayl Yükləməsə:** Qiymətləndirmə dəlillərinin yüklənməsi.
  (File Upload: Upload evaluation evidence.)
* **Email Sistemi:** Bildirişlər, şifrə bərpası, qeydiyyat təsdiqi.
  (Email System: Notifications, password reset, registration confirmation.)
* **Sələhiyyət Modulu:** Hər rəqib əlavə edilə bilən "qiymətləndirici" rəqəmlə kontrol edilir.
  (Permissions Module: Evaluation weights for each evaluator can be defined.)

---

## QURAŞDIRMA VƏ İŞƏ SALMA

(Installation and Deployment)

### 1. Layihəni Klonlayın

(Clone the Project)

```bash
git clone https://github.com/.../dovlet_qurum_qiymetlendirme.git
cd dovlet_qurum_qiymetlendirme
```

### 2. Virtual Mühit Hazırlayın

(Create Virtual Environment)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Asılılıqları Quraşdırın

(Install Dependencies)

```bash
pip install -r requirements.txt
```

### 4. Sistem Kitabxanaları (Windows)

(System Libraries for Windows)

* WeasyPrint üçün GTK3
  (GTK3 for WeasyPrint)
* makemessages üçün gettext (bin yolunu PATH-a daxil edin)
  (gettext for `makemessages` - add bin path to system PATH)

### 5. .env Faylı

(.env File)

* `.env.example` faylını `.env` adlandırın.
  (Rename `.env.example` to `.env`.)
* Parametrləri doldurun: `SECRET_KEY`, `DEBUG`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.
  (Fill in the required parameters: `SECRET_KEY`, `DEBUG`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.)

### 6. Miqrasiyalar və Komandalar

(Migrations and Commands)

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py compilemessages
python manage.py createsuperuser
python manage.py runserver
```

---

## İstifadə Olunan Texnologiyalar

(Technologies Used)

* **Backend:** Django, Python
* **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js
* **Verilənlər Bazası:** SQLite3 (inkisaf), PostgreSQL (istehsalat)
  (Database: SQLite3 for development, PostgreSQL for production)
* **Paketlər:**

  * `django-crispy-forms`, `crispy-bootstrap5`
  * `django-jazzmin` (admin temasi)
  * `django-simple-history` (tarixçə)
  * `weasyprint` (PDF ixrac)
  * `openpyxl` (Excel ixrac)
  * `python-dotenv` (mühit dəyişkənləri)

---

## Gələcək Gənişləndirilmələr (Roadmap)

(Future Enhancements)

* ✅ Mobil əlavə versiyası (Flutter)
  (Mobile app version with Flutter)
* ✅ AI dəstəkli qiymətləndirmə üsulları (machine learning əsaslı analiz)
  (AI-supported evaluation using machine learning analysis)
* ✅ HRMS sistemlərinə REST API vasitəsilə inteqrasiya
  (Integration with HRMS systems via REST API)

Bu sistem, istənilən dövlət və ya özəl qurumun iç strukturlarına asanlıqla uyğunlaşdırıla biləcək şəkildə qurulmuşdur.
(This system is designed to be easily adaptable to the internal structure of any public or private organization.)
