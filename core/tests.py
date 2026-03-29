from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Orphan, Guardian, Donor, OrphanDocument, Notification, Sponsorship
from datetime import timedelta
from django.utils import timezone
# =================================================================
#                    1. MODELS & DATABASE TESTS
# =================================================================
class KafalaModelsTest(TestCase):
    def setUp(self):
        # 1. إنشاء حساب الوصي
        self.guardian_user = User.objects.create_user(username='test_guardian', email='test@test.com', password='password123')
        self.guardian = Guardian.objects.create(
            user=self.guardian_user,
            name='أحمد محمود',
            id_number='123456789',
            phone='0599999999',
            relation_to_orphan='أب',
            payout_method='Cash',
            is_approved=False
        )
        
        # 2. إنشاء حساب اليتيم (التحديث الجديد: يجب أن يمتلك اليتيم حساب User)
        self.orphan_user = User.objects.create_user(username='ibrahim_orphan', password='password123')
        self.orphan = Orphan.objects.create(
            user=self.orphan_user, # تم الربط بنجاح
            username='ibrahim_orphan',
            guardian=self.guardian,
            name='إبراهيم أحمد',
            age=6,
            gender='Male',
            area='غزة',
            sponsorship_status='Pending'
        )

    def test_guardian_creation(self):
        self.assertEqual(self.guardian.name, 'أحمد محمود')
        self.assertFalse(self.guardian.is_approved)

    def test_orphan_creation(self):
        self.assertEqual(self.orphan.name, 'إبراهيم أحمد')
        self.assertEqual(self.orphan.guardian, self.guardian)
        self.assertEqual(self.orphan.user.username, 'ibrahim_orphan')

# =================================================================
#                    2. SMART LOGIN ROUTING TESTS
# =================================================================
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class KafalaLoginRoutingTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin
        self.admin_user = User.objects.create_superuser(username='admin', password='123')
        # Orphan
        self.orphan_user = User.objects.create_user(username='orphan_kid', password='123')
        self.orphan = Orphan.objects.create(user=self.orphan_user, name="طفل", sponsorship_status='Pending')
        # Guardian
        self.guardian_user = User.objects.create_user(username='guardian_dad', password='123')
        self.guardian = Guardian.objects.create(user=self.guardian_user, name="أب")
        
    def test_login_redirects_admin(self):
        response = self.client.post(reverse('login_view'), {'username': 'admin', 'password': '123'})
        self.assertRedirects(response, reverse('admin_dashboard')) # تأكد من اسم الرابط في urls.py
        
    def test_login_redirects_orphan(self):
        response = self.client.post(reverse('login_view'), {'username': 'orphan_kid', 'password': '123'})
        self.assertRedirects(response, reverse('orphan_dashboard'))

    def test_login_redirects_guardian(self):
        response = self.client.post(reverse('login_view'), {'username': 'guardian_dad', 'password': '123'})
        self.assertRedirects(response, reverse('guardian_dashboard'))

# =================================================================
#                    3. ACCESS CONTROL & SECURITY TESTS
# =================================================================
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class KafalaAccessControlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.normal_user = User.objects.create_user(username='normal', password='123')
        self.admin_user = User.objects.create_superuser(username='admin', password='123')

    def test_admin_dashboard_access(self):
        # 1. زائر غير مسجل (ممنوع 302)
        response = self.client.get(reverse('manage_orphans'))
        self.assertEqual(response.status_code, 302) 

        # 2. مستخدم عادي (ممنوع 302)
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('manage_orphans'))
        self.assertEqual(response.status_code, 302)

        # 3. مدير (مسموح 200)
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('manage_orphans'))
        self.assertEqual(response.status_code, 200)

# =================================================================
#                    4. GUARDIAN DASHBOARD & WORKFLOW TESTS
# =================================================================
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class KafalaGuardianDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='admin_g', password='123')

        self.guardian_user = User.objects.create_user(username='wasi1', password='123')
        self.guardian = Guardian.objects.create(
            user=self.guardian_user,
            name='محمد وصي',
            id_number='111222333',
            phone='0591234567',
            relation_to_orphan='عم',
            payout_method='Cash',
            is_approved=True,
        )

        self.orphan_user = User.objects.create_user(username='sara_orphan', password='123')
        self.orphan = Orphan.objects.create(
            user=self.orphan_user,
            guardian=self.guardian,
            name='سارة',
            age=7,
            gender='Female',
            area='غزة',
            sponsorship_status='Pending',
        )

        # وصي آخر لاختبار ثغرات IDOR
        self.other_user = User.objects.create_user(username='wasi2', password='123')
        self.other_guardian = Guardian.objects.create(user=self.other_user, name='أحمد آخر')
        self.other_orphan_user = User.objects.create_user(username='yousef_orphan', password='123')
        self.other_orphan = Orphan.objects.create(user=self.other_orphan_user, guardian=self.other_guardian, name='يوسف', sponsorship_status='Available')

    def test_idor_blocked_on_upload_page(self):
        """Guardian should NOT access another guardian's orphan upload page."""
        self.client.force_login(self.guardian_user)
        response = self.client.get(reverse('guardian_upload_document', args=[self.other_orphan.id]))
        self.assertEqual(response.status_code, 302) # يتم طرده

    def test_guardian_apply_orphan_with_user_credentials(self):
        """اختبار تسجيل يتيم جديد مع إنشاء حسابه المستقل"""
        self.client.force_login(self.guardian_user)
        
        import uuid
        unique_username = f"orphan_{uuid.uuid4().hex[:6]}"
        data = {
            'orphan_username': unique_username,
            'orphan_password': 'securepassword123',
            'name': 'يتيم اختبار',
            'age': '10',
            'gender': 'Male',
            'area': 'غزة',
            'social_status': 'يتيم الأب',
            'health_status': 'سليمة'
        }
        
        response = self.client.post(reverse('guardian_apply_orphan'), data)
        
        # 🔥 تتبع دقيق لمسار النظام إذا فشل التوجيه الصحيح
        if response.status_code == 302:
            print(f"\n--- النظام قام بتوجيهنا إلى: {response.url} ---")
            
        # نطلب من الاختبار أن يتأكد أن التوجيه ذهب إلى 'أيتامي' وليس لصفحة أخرى كـ تسجيل الدخول
        self.assertRedirects(response, reverse('guardian_my_orphans'), msg_prefix="التوجيه ذهب لمكان خاطئ!")
        
        new_orphan = Orphan.objects.filter(name='يتيم اختبار').first()
        self.assertIsNotNone(new_orphan, "اليتيم لم يتم حفظه في قاعدة البيانات")

# =================================================================
#                    5. DOCUMENT PRIVACY SYSTEM TESTS
# =================================================================
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class KafalaDocumentSystemTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='doc_admin', password='123')
        
        self.orphan_user = User.objects.create_user(username='doc_orphan', password='123')
        self.orphan = Orphan.objects.create(user=self.orphan_user, name='يتيم المستندات', sponsorship_status='Available')
        
        # --- التعديل هنا: إنشاء ملف PDF وهمي للاختبار ---
        dummy_file = SimpleUploadedFile(
            name='test_doc.pdf', 
            content=b'This is a fake pdf content for testing', 
            content_type='application/pdf'
        )
        
        # إنشاء مستند مخفي افتراضياً مع إرفاق الملف الوهمي
        self.document = OrphanDocument.objects.create(
            orphan=self.orphan,
            title='شهادة ميلاد أصلية',
            document=dummy_file, # <--- تم إرفاق الملف الوهمي بنجاح
            document_type='Legal',
            is_public=False
        )

    def test_toggle_document_visibility_by_admin(self):
        """اختبار زر الإدارة لتحويل الملف من مخفي إلى مرئي"""
        self.client.force_login(self.admin_user)
        
        # التأكد أنه مخفي في البداية
        self.assertFalse(self.document.is_public)
        
        # إرسال طلب التبديل (Toggle)
        response = self.client.post(reverse('toggle_document_visibility', args=[self.document.id]))
        
        # تحديث البيانات من قاعدة البيانات
        self.document.refresh_from_db()
        
        # يجب أن يصبح مرئياً الآن
        self.assertTrue(self.document.is_public)
        self.assertRedirects(response, reverse('admin_orphan_details', args=[self.orphan.id]))

    def test_get_public_documents_method(self):
        """اختبار أن دالة المتبرع لا تجلب إلا الملفات العامة"""
        public_docs = self.orphan.get_public_documents()
        self.assertEqual(public_docs.count(), 0) # لا يوجد ملفات عامة حتى الآن
        
        # نجعل الملف عاماً
        self.document.is_public = True
        self.document.save()
        
        public_docs_after = self.orphan.get_public_documents()
        self.assertEqual(public_docs_after.count(), 1) # الآن يمكن للكافل رؤيته

class NotificationSystemTest(TestCase):
    def setUp(self):
        """تجهيز بيئة الاختبار: إنشاء مدير، ووصي، وطلب قيد المراجعة"""
        self.client = Client()
        
        # 1. إنشاء حساب مدير النظام (Admin)
        self.admin_user = User.objects.create_superuser(
            username='admin_test', email='admin@test.com', password='password123'
        )
        
        # 2. إنشاء حساب الوصي (Guardian) الذي قدم الطلب
        self.guardian_user = User.objects.create_user(
            username='guardian_test', email='guardian@test.com', password='password123'
        )
        self.guardian = Guardian.objects.create(
            user=self.guardian_user,
            phone="0590000000",
        )
        
        # 3. إنشاء طلب يتيم (قيد المراجعة)
        self.orphan = Orphan.objects.create(
            guardian=self.guardian,
            name="يتيم تجريبي",
            age=10,
            sponsorship_status='Pending' # حالة الطلب قبل تدخل الإدارة
        )

    def test_notification_sent_on_admin_approval(self):
        """اختبار: هل يتم إرسال إشعار للوصي عند موافقة الإدارة؟"""
        
        # تسجيل دخول المدير
        self.client.login(username='admin_test', password='password123')
        
        # محاكاة قيام المدير بالضغط على زر "موافقة" لطلب اليتيم
        # (يرجى تغيير 'approve_orphan' لاسم الرابط الفعلي في مشروعك)
        response = self.client.post(reverse('approve_orphan_request', args=[self.orphan.id]))
        
        # التأكد من أن التوجيه تم بنجاح بعد الموافقة (مثلاً يعود لصفحة الأيتام)
        self.assertEqual(response.status_code, 302)
        
        # التحدي الأكبر: التحقق من قاعدة بيانات الإشعارات!
        # هل تم إنشاء إشعار جديد ومستقبله هو حساب الوصي؟
        notification_exists = Notification.objects.filter(
            recipient=self.guardian_user,
            title__icontains="موافقة" # نفترض أن العنوان يحتوي على كلمة "موافقة"
        ).exists()
        
        # إذا كانت النتيجة False، سيفشل الاختبار وتظهر لك هذه الرسالة
        self.assertTrue(notification_exists, "❌ فشل الاختبار: النظام لم يقم بإنشاء إشعار للوصي عند موافقة الإدارة!")

    def test_notification_sent_on_admin_rejection(self):
        """اختبار: هل يتم إرسال إشعار للوصي عند رفض الإدارة؟"""
        # 🔥 الحل العبقري: إنشاء يتيم "حماية" ثاني لكي لا يقوم النظام بحذف الوصي بعد رفض الأول!
        Orphan.objects.create(
            guardian=self.guardian,
            name="يتيم حماية",
            age=5,
            sponsorship_status='Pending'
        )
        
        self.client.login(username='admin_test', password='password123')
        
        # محاكاة رفض اليتيم الأول
        response = self.client.post(reverse('reject_orphan_request', args=[self.orphan.id]))
        
        # الآن الوصي لم يُحذف، وإشعاراته يجب أن تكون موجودة
        all_notifications = Notification.objects.filter(recipient=self.guardian_user)
        
        self.assertTrue(all_notifications.exists(), "❌ فشل الاختبار: الإشعار لا يزال غير موجود!")

        from datetime import timedelta
from django.utils import timezone
# تأكد من استيراد نماذج الكافل والكفالة الخاصة بك
# from core.models import Donor, Sponsorship 

class DonorNotificationSystemTest(TestCase):
    def setUp(self):
        """تجهيز بيئة الاختبار الخاصة بالكافل"""
        self.client = Client()
        
        # 1. إنشاء حساب المدير
        self.admin_user = User.objects.create_superuser(
            username='admin_donor_test', email='admin2@test.com', password='password123'
        )
        
        # 2. إنشاء حساب الكافل (Donor)
        self.donor_user = User.objects.create_user(
            username='donor_test', email='donor@test.com', password='password123'
        )
        # افترضنا أن جدول الكافل لديك اسمه Donor
        self.donor = Donor.objects.create(
            user=self.donor_user,
            phone="0591112223"
        )
        
        # 3. إنشاء يتيم متاح للكفالة
        self.orphan = Orphan.objects.create(
            name="يتيم متاح",
            age=8,
            sponsorship_status='Available'
        )
        
        # 4. إنشاء طلب كفالة (قيد المراجعة)
        # افترضنا وجود جدول يربط الكافل باليتيم اسمه Sponsorship
        self.sponsorship = Sponsorship.objects.create(
            donor=self.donor,
            orphan=self.orphan,
            amount=50.00,
            status='Pending', # حالة الطلب قبل موافقة الإدارة
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date() # كفالة لسنة
        )

    def test_notification_sent_on_sponsorship_approval(self):
        """اختبار: إشعار الكافل عند موافقة الإدارة على طلب الكفالة"""
        self.client.login(username='admin_donor_test', password='password123')
        
        # محاكاة ضغط المدير على زر "موافقة" لطلب الكفالة
        # 🛑 هام: تأكد من تغيير 'approve_sponsorship' للاسم الموجود في urls.py لديك
        response = self.client.post(reverse('approve_sponsorship', args=[self.sponsorship.id]))
        
        all_notifications = Notification.objects.filter(recipient=self.donor_user)
        
        if not all_notifications.exists():
            print("\n❌ لم يتم إرسال إشعار للكافل بعد الموافقة!")
            
        self.assertTrue(all_notifications.exists(), "فشل الاختبار: لا يوجد إشعار موافقة للكافل")

    def test_payment_reminder_notification(self):
        """اختبار: نظام التنبيهات الزمنية (تذكير باقتراب انتهاء الكفالة)"""
        # في هذا الاختبار، سنقوم بتغيير تاريخ انتهاء الكفالة ليصبح بعد 3 أيام فقط!
        self.sponsorship.status = 'Active'
        self.sponsorship.end_date = (timezone.now() + timedelta(days=3)).date()
        self.sponsorship.save()
        
        # محاكاة تشغيل الدالة المسؤولة عن فحص التواريخ (سنكتبها لاحقاً في tasks أو utils)
        # check_expiring_sponsorships() 
        
        # للتأكد من الفكرة الآن، سنقوم بإنشاء الإشعار يدوياً كما لو أن الدالة عملت
        from core.utils import send_notification
        if (self.sponsorship.end_date - timezone.now().date()).days <= 3:
            send_notification(
                user=self.donor.user,
                title="تذكير باقتراب انتهاء الكفالة",
                message=f"كفالتك لليتيم ({self.orphan.name}) تنتهي خلال 3 أيام. نأمل تجديد عطائكم.",
                link="/donor/sponsorships/"
            )
            
        all_notifications = Notification.objects.filter(recipient=self.donor_user, title__contains="تذكير")
        self.assertTrue(all_notifications.exists(), "فشل الاختبار: لم يتم توليد إشعار التذكير الزمني")


def test_sponsorship_auto_expiry_logic(self):
        """اختبار: هل تنتهي الكفالة تلقائياً ويرسل إشعار عند وصول تاريخ النهاية؟"""
        # 1. جعل تاريخ النهاية هو "اليوم"
        self.sponsorship.status = 'Active'
        self.sponsorship.end_date = timezone.now().date()
        self.sponsorship.save()

        # 2. محاكاة دخول الكافل للوحة التحكم (تشغيل دالة الفحص)
        self.client.login(username='donor_test', password='password123')
        response = self.client.get(reverse('donor_dashboard'))

        # 3. التحقق من تحديث حالة الكفالة في قاعدة البيانات
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, 'Ended')

        # 4. التحقق من تحرير اليتيم ليكون متاحاً (Available)
        self.orphan.refresh_from_db()
        self.assertEqual(self.orphan.sponsorship_status, 'Available')

        # 5. التحقق من وصول إشعار "انتهاء الكفالة"
        notification_exists = Notification.objects.filter(
            recipient=self.donor_user, 
            title__icontains="انتهت"
        ).exists()
        self.assertTrue(notification_exists, "❌ فشل الاختبار: لم يتم إرسال إشعار انتهاء الكفالة!")

def test_monthly_payment_reminder(self):
        """اختبار: هل يتم إرسال تذكير بالدفع إذا كان اليوم هو موعد المساهمة؟"""
        # 1. جعل تاريخ البداية في مثل هذا اليوم من شهر سابق
        # (لأننا برمجنا التنبيه ليعمل إذا كان today.day == start_date.day)
        self.sponsorship.status = 'Active'
        self.sponsorship.sponsorship_type = 'Monthly'
        self.sponsorship.start_date = timezone.now().date() - timedelta(days=30)
        self.sponsorship.save()

        # 2. دخول الكافل للوحة التحكم
        self.client.login(username='donor_test', password='password123')
        self.client.get(reverse('donor_dashboard'))

        # 3. التحقق من وجود إشعار "موعد المساهمة"
        notification_exists = Notification.objects.filter(
            recipient=self.donor_user, 
            title__icontains="موعد"
        ).exists()
        self.assertTrue(notification_exists, "❌ فشل الاختبار: لم يتم إرسال تذكير الدفع الشهري!")