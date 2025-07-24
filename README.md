# Q360 - 360 Dərəcə Performans Qiymətləndirmə Sistemi

## 360 Degree Appraisal System

**Q360** – dövlət idarələri, ictimai qurumlar və ya özəl sektor təşkilatları üçün nəzərdə tutulmuş, əməkdaşların kompetensiyaları üzrə obyektiv və çoxşaxəli qiymətləndirilməni təmin edən tam funksional, modul-əsaslı və müasir bir veb platformadır. Bu sistem Django framework-u üzərində qurulmuşdur və istinad edilən beynəlxalq qiymətləndirmə standartlarını əsas götürür. Sistem istənilən mürəkkəblikdəki təşkilati iyerarxiyaya uyğunlaşa bilər və performansın effektiv idarə edilməsini təmin edir.

Q360 is a fully functional and modern web platform developed with the Django framework, designed to provide objective and multi-faceted competency-based evaluation of employees in public sector bodies, governmental agencies, and private organizations. The system is modular, highly extensible, and adheres to international assessment standards, making it suitable for managing performance in even the most complex hierarchical structures.

---

## 🔹 Əsas Funksionallıq (Core Functionality)

### ✔️ Rol Əsaslı Dinamik İdarəetmə (Role-Based Dynamic Management)

//Sistem dörd əsas istifadəçi rolunu dəstəkləyir, hər biri konkret funksionallıqlara malikdir və sistem daxilində fərqli icazələrə sahibdir:

* **Superadmin**: Bütün sistemin tam idarəetməsini həyata keçirir. Qiymətləndirmə dövrlərini planlaşdırır və yaradır, təşkilati struktur elementlərini (nazirlik, idarə, şöbə, sektor və s.) idarə edir, istifadəçiləri təyin edir və sistemin ümumi performansını ölçən analitik hesabatlara çıxış əldə edir.

* **Admin**: İdarə və ya müəssisə daxilində işçilərin və rəhbərlərin qeydiyyatını aparır, qiymətləndirmə suallarının bankını idarə edir, strukturun icazə və parametrlərini tənzimləyir. Bu rol daha çox `Django Admin Panel` üzərindən funksional idarəetmə aparır.

* **Rəhbər (Manager)**: Tabeliyində olan əməkdaşları qiymətləndirir, onların performans statistikası ilə tanış olur və fərdi hesabatları təhlil edir. Eyni zamanda, komandasının ümumi kompetensiya paylanmasını və inkişaf sahələrini vizual şəkildə izləyə bilir.

* **İşçi (Employee)**: Özünü qiymətləndirir, birbaşa rəhbərinə və komanda yoldaşlarına rəy verir. Nəticələrə əsaslanaraq şəxsi performans hesabatına baxır, yazılı rəylərlə tanış olur və fərdi inkişaf planını nəzərdən keçirir.

---

### ✔️ Avtomatlaşdırılmış Qiymətləndirmə Prosesi

Qiymətləndirmə prosesləri Superadmin tərəfindən idarə olunur və ağıllı sistem vasitəsilə optimallaşdırılır:

* **Dinamik Qiymətləndirmə Kampaniyaları**: Müəyyən tarix aralığına uyğun qiymətləndirmə mərhələləri yaradılır. Hər kampaniya daxilində işçi-profiller, kompetensiya qrupları və qiymətləndirmə meyarları avtomatik şəkildə tətbiq olunur.

* **Ağıllı Qiymətləndirici Təyinat Sistemi**: Hər bir işçiyə onun özü, rəhbəri və təsadüfi seçilmiş iki komanda yoldaşı tərəfindən qiymətləndirmə aparılır. Bu 360 dərəcə modeli obyekivliyi təmin edir və sistemin şəffaflığını artırır.

* **Avtomatik Bildiriş Sistemi**: Qiymətləndirmə dövrləri yaxınlaşdıqda və ya yeni qiymətləndirici təyin edildikdə, sistem istifadəçilərə avtomatik e-poçt və ya daxili bildiriş vasitəsilə məlumat verir.

---

### ✔️ Dərin Hesabatlar və Analitik Alətlər

* **Fərdi Hesabatlar**: Radar chart formasında vizuallaşdırılmış kompetensiya balları, həmçinin anonim şəkildə toplanmış yazılı rəy bölməsi ilə işçinin ümumi və detallı performans portreti təqdim olunur.

* **Performans Tarixçəsi (Trend Analysis)**: Line chart vasitəsilə müxtəlif qiymətləndirmə dövrləri üzrə işçinin inkişaf dinamikası təhlil edilir.

* **Boşluq Analizi (Gap Analysis)**: İşçinin özünə verdiyi qiymətlərlə başqalarının ona verdiyi qiymətlər arasındakı fərq göstərilərək inkişaf sahələri müəyyən olunur.

* **İxrac Modulu**: İstifadəçi fərdi hesabatları PDF və Excel formatında ixrac edə, rəhbər isə struktur və qurum səviyyəsində hesabatları yükləyə bilir.

---

### ✔️ Fərdi İnkişaf Planı (Individual Development Plan)

* Rəhbərlər qiymətləndirmə nəticələrinə əsaslanaraq işçilərinə konkret inkişaf hədəfləri təyin edir.
* Hər bir hədəf SMART modelinə (Specific, Measurable, Achievable, Relevant, Time-bound) uyğun formalaşdırılır.
* İşçilər bu hədəflərin icra statusunu izləyir və onların tamamlanma vəziyyətini yeniləyə bilir.

---

### ✔️ UX/UI və Multidillilik

* **Admin Panel**: `django-jazzmin` teması ilə tamamilə yenidən dizayn olunmuş, istifadəçi dostu və peşəkar görünüşlü idarəetmə paneli.
* **Responsiv Formlar**: `crispy-bootstrap5` vasitəsilə qurulmuş mobil uyğun dizayn və müasir görünüş.
* **Dark/Light Tema**: Vizual rahatlıq üçün istifadəçi seçimli qaranlıq və işıqlı rejim dəstəyi.
* **Çoxdilli Dəstək**: `gettext` əsasında işləyən, hal-hazırda Azərbaycan və İngilis dillərini dəstəkləyən tam tərcümə modulu.

---

### ✔️ Təhlükəsizlik və İdarəetmə

* **Audit Trail (Tarixçə)**: `django-simple-history` vasitəsilə istifadəçi və sistem fəaliyyətləri izlənilir. Hər hansı dəyişiklik (yaradılma, yenilənmə, silinmə) tarixçədə qeydə alınır.
* **Gizli Məlumatların Qorunması**: `python-dotenv` ilə bütün həssas konfiqurasiya dəyərləri .env faylında saxlanılır və versiya nəzarətinə daxil edilmir.
* **Avtomatlaşdırılmış Testlər**: Giriş, çıxış, qeydiyyat, qiymətləndirmə və IDP axınları üçün sınaq modulları ilə stabillik təmin olunur.

---

## ⚙️ Quraşdırma və İşə Salma (Installation and Deployment)

### 1. Layihəni Klonlayın

```bash
git clone https://github.com/MuradoffTehmez/Q360.git
cd Q360
```

### 2. Virtual Mühit Yaradın

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Asılılıqları Quraşdırın

```bash
pip install -r requirements.txt
```

### 4. Sistem Kitabxanaları (Windows üçün)

* WeasyPrint üçün GTK3
* Tərcümə üçün gettext (və PATH-a əlavə edilməlidir)

### 5. .env Faylını Hazırlayın

* `.env.example` faylını `.env` adlandırın və aşağıdakı parametrləri daxil edin:

  * `SECRET_KEY`, `DEBUG`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

### 6. Miqrasiyalar və Əməliyyat Komandaları

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py compilemessages
python manage.py createsuperuser
python manage.py runserver
```

---

## 💻 İstifadə Olunan Texnologiyalar (Technologies Used)

* **Backend**: Django (Python)
* **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js
* **Verilənlər Bazası**: SQLite3 (lokal inkişaf üçün), PostgreSQL (istehsalat üçün)

### Əlavə Paketlər:

* `django-crispy-forms`, `crispy-bootstrap5` – responsiv formalar
* `django-jazzmin` – admin panel dizaynı
* `django-simple-history` – tarixçə (audit trail)
* `weasyprint` – PDF hesabat generasiyası
* `openpyxl` – Excel ixrac funksiyası
* `python-dotenv` – mühit dəyişənlərinin idarə olunması
* 
---

## 🚀 Gələcək Genişləndirilmələr (Roadmap)

* **REST API İnterfeysi**: HRMS (İnsan Resurslarının İdarəedilməsi Sistemi) ilə inteqrasiya üçün tam RESTful API hazırlanacaq.
* **Asinxron Tapşırıqlar**: `Celery` və `Redis` vasitəsilə arxa planda e-poçt bildirişləri və hesabat generasiyası.
* **AI Dəstəyi**: Machine Learning modulu ilə toplanmış rəylər əsasında avtomatik inkişaf tövsiyələri yaradılacaq.

---

> **Q360 – dövlət və özəl sektor təşkilatları üçün çevik, etibarlı və genişlənə bilən performans qiymətləndirmə həllidir.**
