# Q360 Təhlükəsizlik Siyasəti

## Dəstəklənən Versiyalar

Hazırda layihənin yalnız ən son versiyası aktiv şəkildə dəstəklənir və təhlükəsizlik yeniləmələri alır.

| Versiya | Dəstəklənir          |
| ------- | ------------------ |
| 1.0.0   | :white_check_mark: |

## Təhlükəsizlik Boşluğunun Bildirilməsi

Q360 layihəsində təhlükəsizliyi çox ciddiyə alırıq. Əgər hər hansı bir təhlükəsizlik boşluğu aşkar etsəniz, bunu məxfi şəkildə bizə bildirməyinizi xahiş edirik. Zəhmət olmasa, problemi ictimai forumlarda və ya GitHub-da müzakirə etməyin.

Aşkar etdiyiniz boşluğu bizə bildirmək üçün, zəhmət olmasa, aşağıdakı e-poçt ünvanına detallı bir məlumat göndərin:

**muradoffcode@gmail.com**

Yaxşı bir təhlükəsizlik hesabatı aşağıdakıları ehtiva etməlidir:
- Boşluğun ətraflı təsviri.
- Problemin potensial təsirinin izahı.
- Problemi təkrar yaratmaq üçün addım-addım təlimatlar (Proof of Concept).

Hesabatınızı aldıqdan sonra 48 saat ərzində sizə cavab verəcəyimizə və problemi araşdırmağa başlayacağımıza söz veririk.

## Tətbiq Olunmuş Təhlükəsizlik Tədbirləri

Q360 sistemi, Django framework-unun təqdim etdiyi bir çox daxili təhlükəsizlik mexanizmlərindən istifadə edir:
- **CSRF (Cross-Site Request Forgery) Qoruması:** Bütün POST sorğuları CSRF tokenləri ilə qorunur.
- **XSS (Cross-Site Scripting) Qoruması:** Django şablonları, daxil edilən məlumatları avtomatik olaraq "escape" edərək XSS hücumlarının qarşısını alır.
- **SQL Injection Qoruması:** Django ORM, verilənlər bazasına olan sorğuları parametrləşdirərək SQL Injection hücumlarına qarşı qoruma təmin edir.
- **Həssas Məlumatların Təcrid Edilməsi:** `SECRET_KEY`, e-poçt şifrələri və digər həssas məlumatlar `.env` faylı vasitəsilə koddan kənarda saxlanılır.
- **Rol Əsaslı İcazələr:** Sistemdəki hər bir funksiya, istifadəçinin roluna (`İşçi`, `Rəhbər`, `Superadmin`) əsaslanan sərt icazə yoxlamalarından keçir.
- **Dəyişikliklərin Tarixçəsi (Audit Log):** `django-simple-history` paketi vasitəsilə bütün vacib məlumatlar üzərində edilən dəyişikliklər (kim, nə vaxt, nəyi dəyişdi) qeydə alınır.
