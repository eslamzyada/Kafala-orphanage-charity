from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Orphan, Guardian, Donor

class KafalaModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_guardian', email='test@test.com', password='password123')
        self.guardian = Guardian.objects.create(
            user=self.user,
            name='أحمد محمود',
            id_number='123456789',
            phone='0599999999',
            relation_to_orphan='أب', # Added required field
            payout_method='Cash',
            is_approved=False
        )
        self.orphan = Orphan.objects.create(
            username='test_guardian',
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
        self.assertEqual(self.orphan.sponsorship_status, 'Pending')


# We use override_settings here to stop Django from throwing an error if an image is missing during a test.
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class KafalaAccessControlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.normal_user = User.objects.create_user(username='normal', password='123')
        self.admin_user = User.objects.create_superuser(username='admin', password='123')

    def test_admin_dashboard_access(self):
        # 1. زائر غير مسجل (ممنوع)
        response = self.client.get(reverse('manage_orphans'))
        self.assertEqual(response.status_code, 302) 

        # 2. مستخدم عادي (ممنوع)
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('manage_orphans'))
        self.assertEqual(response.status_code, 302)

        # 3. مدير (مسموح)
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('manage_orphans'))
        self.assertEqual(response.status_code, 200)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class KafalaWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='admin', email='admin@test.com', password='123')
        
        self.guardian_user = User.objects.create_user(username='khalid', email='khalid@test.com', password='123')
        
        self.guardian = Guardian.objects.create(
            user=self.guardian_user, 
            name='خالد', 
            phone='0590000000',
            id_number='123456789',
            relation_to_orphan='عم', # Added required field
            payout_method='Cash',
            is_approved=False
        )
        
        self.orphan = Orphan.objects.create(
            username='khalid',
            guardian=self.guardian, 
            name='سارة خالد', 
            sponsorship_status='Pending'
        )

    def test_register_new_guardian_and_orphan(self):
        data = {
            'user_type': 'supported',
            'guardian_username': 'new_user',
            'guardian_password': 'password123',
            'guardian_email': 'new@test.com',
            'guardian_name': 'سعيد علي',
            'guardian_id': '987654321',
            'guardian_phone': '0591234567',
            'guardian_relation': 'جد',
            'orphan_name': 'يوسف سعيد',
            'orphan_gender': 'Male',
            'payout_method': 'Bank',
            'orphan_age': '8',
            'orphan_area': 'الرمال',
            'orphan_social': 'يتيم الأب',
            'orphan_health': 'ممتازة'
        }
        response = self.client.post(reverse('register_view'), data)
        self.assertTrue(User.objects.filter(username='new_user').exists())
        self.assertTrue(Guardian.objects.filter(name='سعيد علي').exists())

    def test_admin_approve_orphan(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('approve_orphan_request', args=[self.orphan.id]))
        
        self.orphan.refresh_from_db()
        self.guardian.refresh_from_db()
        
        self.assertEqual(self.orphan.sponsorship_status, 'Available')
        self.assertTrue(self.guardian.is_approved)

    def test_admin_reject_orphan(self):
        self.client.force_login(self.admin_user)
        orphan_id = self.orphan.id
        response = self.client.post(reverse('reject_orphan_request', args=[orphan_id]))
        
        self.assertFalse(Orphan.objects.filter(id=orphan_id).exists())

    def test_orphan_edit_profile(self):
        self.client.force_login(self.guardian_user)
        
        data = {
            'age': 10,
            'gender': 'Female',
            'health_status': 'ممتازة',
            'area': 'رفح',
            'social_status': 'يتيم الأب',
            'guardian_phone': '0591112223',
            'payout_method': 'Wallet',
            'payout_details': '123456',
            'guardian_email': 'khalid_new@test.com'
        }
        
        response = self.client.post(reverse('orphan_edit_profile'), data)
        
        self.orphan.refresh_from_db()
        self.guardian.refresh_from_db()
        self.guardian_user.refresh_from_db()
        
        self.assertEqual(self.orphan.area, 'رفح')
        self.assertEqual(self.orphan.age, 10)
        self.assertEqual(self.guardian.payout_method, 'Wallet')
        self.assertEqual(self.guardian_user.email, 'khalid_new@test.com')