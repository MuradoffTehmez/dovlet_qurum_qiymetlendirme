# 360 Dərəcə Qiymətləndirmə Sistemi

Bu, Django web framework-u ilə yaradılmış, dövlət orqanları və ya təşkilatlar üçün nəzərdə tutulmuş hərtərəfli 360 dərəcə performans qiymətləndirmə platformasıdır.

## Əsas Funksiyalar

- **Çoxşaxəli İstifadəçi Rolları:** İşçi, Rəhbər, Superadmin və Admin üçün xüsusi panellər və icazələr.
- **Dinamik Qiymətləndirmə Prosesi:** Superadmin tərəfindən yeni qiymətləndirmə dövrlərinin yaradılması və kimin kimi qiymətləndirəcəyinin avtomatik təyin edilməsi (özünü, rəhbəri, komanda yoldaşlarını).
- **Analitik Hesabatlar:** Hər bir işçi üçün kompetensiyalar üzrə detallı analiz və performans tarixçəsini göstərən interaktiv qrafiklər (Radar və Line chart).
- **Fayl İxracı:** Fərdi və ümumi hesabatların PDF və Excel formatlarında yüklənməsi.
- **Peşəkar İstifadəçi Təcrübəsi:**
  - Çoxdilli dəstək (Azərbaycan/İngilis).
  - Qaranlıq/İşıqlı rejim (Dark/Light Mode).
  - Tam Qeydiyyat, Giriş və Şifrə Bərpası axını.
- **Təhlükəsizlik və Hesabatlılıq:** Bütün vacib məlumat dəyişikliklərini izləyən Audit Trail (Tarixçə) sistemi.
- **Müasir Dizayn:** `Bootstrap 5`, `django-crispy-forms` və `django-jazzmin` ilə qurulmuş səliqəli və mobil uyğun interfeyslər.

## Quraşdırma və İşə Salma Təlimatları

1.  **Layihəni Klonlayın:**
    ```bash
    git clone <repository_url>
    cd dovlet_qurum_qiymetlendirme
    ```

2.  **Virtual Mühit Yaradın və Aktivləşdirin:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Asılılıqları Quraşdırın:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Sistem Asılılıqlarını Quraşdırın (Windows üçün):**
    - `WeasyPrint` üçün [GTK3](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows) quraşdırın.
    - `makemessages` üçün [gettext](https://mlocati.github.io/articles/gettext-iconv-windows.html) yükləyib, `bin` qovluğunu sistemin `PATH`-ına əlavə edin.

5.  **`.env` Faylını Yaradın:**
    - `.env.example` faylının adını `.env` olaraq dəyişdirin.
    - `.env` faylını açıb, `SECRET_KEY`, `DEBUG`, `EMAIL_HOST_USER` və `EMAIL_HOST_PASSWORD` dəyərlərini öz məlumatlarınızla doldurun.

6.  **Miqrasiyaları Tətbiq Edin:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **Tərcümə Fayllarını Kompilyasiya Edin:**
    ```bash
    python manage.py compilemessages
    ```

8.  **Superadmin Hesabı Yaradın:**
    ```bash
    python manage.py createsuperuser
    ```

9.  **Serveri İşə Salın:**
    ```bash
    python manage.py runserver
    ```
    İndi [http://127.0.0.1:8000/](http://127.0.0.1:8000/) ünvanına daxil ola bilərsiniz.

## İstifadə Olunan Texnologiyalar
- **Backend:** Django, Python
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript, Chart.js
- **Verilənlər Bazas:** SQLite3 (development), PostgreSQL
- **Paketlər:** `django-crispy-forms`, `crispy-bootstrap5`, `django-jazzmin`, `django-simple-history`, `weasyprint`, `openpyxl`, `python-dotenv`