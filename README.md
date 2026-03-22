# 🕊️ منصة "كفالة" لإدارة ورعاية الأيتام
**Kafala - Orphanage Care & Management Platform**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2+-092E20.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📌 عن المشروع (About The Project)
"كفالة" هي منصة إلكترونية متكاملة مبنية بإطار عمل **Django**، تهدف إلى أتمتة وتنظيم عملية كفالة الأيتام وتسهيل التواصل بين الأوصياء (أولياء الأمور) وإدارة المؤسسة الخيرية. يوفر النظام بيئة آمنة وشفافة لتسجيل بيانات الأيتام، رفع المستندات القانونية، وإدارة المعاملات المالية للكفالات.

---

## ✨ المميزات الرئيسية (Key Features)

* 🛡️ **نظام الاعتماد والتدقيق (Approval Workflow):** لا يتم عرض أي يتيم للكفالة إلا بعد مراجعة الإدارة للمستندات القانونية (PDF) واعتماد حساب الوصي.
* 👥 **لوحات تحكم منفصلة (Dashboards):**
  * **الإدارة (Admin):** مراجعة الطلبات المعلقة، إدارة الأيتام والأوصياء، وقبول/رفض التسجيلات.
  * **الوصي (Guardian):** تسجيل الدخول، إضافة أيتام، تعديل تفاصيل الاستلام المالي (حوالة بنكية، محفظة إلكترونية)، وتحديث الحالة الصحية والاجتماعية.
* 🔒 **أمان عالي (Security):** حماية كاملة للمسارات (Routes)، حيث لا يمكن لغير المدراء الوصول لصفحات الإدارة، مع حماية ضد هجمات XSS و CSRF.
* 🧪 **بيئة مختبرة (Fully Tested):** تغطية برمجية (Unit Tests) للتحقق من سلامة قواعد البيانات، الصلاحيات، ودورة حياة النظام.

---

## 🛠️ التقنيات المستخدمة (Tech Stack)

* **الخلفية البرمجية (Backend):** Python, Django 4.x
* **الواجهات (Frontend):** HTML5, CSS3 (Pure CSS Grid & Flexbox), JavaScript
* **قاعدة البيانات (Database):** SQLite (للتطوير) / PostgreSQL (للإنتاج)

---

## 🚀 كيفية تشغيل المشروع محلياً (Local Setup)

اتبع هذه الخطوات لتشغيل المشروع على جهازك الشخصي:

**1. استنساخ المستودع (Clone the repository)**
```bash
git clone [https://github.com/YourUsername/orphanage_backend.git](https://github.com/YourUsername/orphanage_backend.git)
cd orphanage_backend
```
2. إنشاء بيئة عمل افتراضية (Create Virtual Environment):
python -m venv venv

3. تفعيل البيئة الافتراضية (Activate Virtual Environment):
venv\Scripts\activate
4. تثبيت الحزم والمتطلبات (Install Dependencies):
pip install -r requirements.txt
5. تهيئة قاعدة البيانات (Run Migrations):
python manage.py makemigrations
python manage.py migrate

6. إنشاء حساب مدير النظام (Create Superuser):
python manage.py createsuperuser
7. تشغيل الخادم المحلي (Run the Server):
python manage.py runserver
تشغيل الاختبارات البرمجية (Running Tests):
python manage.py test

المطور (Developer): Islam Ziada & Mouaz Al-Rantissi
تخصص علم الحاسوب (Applied Information Technology)
مشروع تخرج (Graduation Project)
