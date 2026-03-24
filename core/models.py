import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

ALLOWED_DOCUMENT_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
ALLOWED_DOCUMENT_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png"]
MAX_DOCUMENT_SIZE_MB = 5
MAX_DOCUMENT_SIZE_BYTES = MAX_DOCUMENT_SIZE_MB * 1024 * 1024

def orphan_document_upload_to(instance, filename):
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    orphan_id = instance.orphan_id or "unknown"
    return f"orphan_documents/orphan_{orphan_id}/{uuid.uuid4().hex}{ext}"

def validate_document_file(upload):
    if upload.size > MAX_DOCUMENT_SIZE_BYTES:
        raise ValidationError(f"File too large. Max size is {MAX_DOCUMENT_SIZE_MB} MB.")
    content_type = getattr(upload, "content_type", None)
    if content_type and content_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValidationError("Unsupported file type.")

class Guardian(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=150, verbose_name="اسم الوصي الرباعي")
    id_number = models.CharField(max_length=20, unique=True, verbose_name="رقم الهوية")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    relation_to_orphan = models.CharField(max_length=50, verbose_name="صلة القرابة (مثال: أم، عم، جد)")
    
    legal_document = models.FileField(upload_to='guardian_docs/', verbose_name="مستند الوصاية")
    
    PAYOUT_CHOICES = [
        ('Bank', 'حوالة بنكية'),
        ('Wallet', 'محفظة إلكترونية (مثل Jawwal Pay)'),
        ('Cash', 'استلام نقدي باليد'),
    ]
    payout_method = models.CharField(max_length=20, choices=PAYOUT_CHOICES, default='Cash', verbose_name="طريقة استلام الكفالة")
    payout_details = models.CharField(max_length=255, blank=True, null=True, verbose_name="رقم الحساب أو رقم المحفظة")
    
    is_approved = models.BooleanField(default=False, verbose_name="تم التحقق من الوصي")

    def __str__(self):
        return self.name

class Orphan(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='orphan_profile')
    username = models.CharField(max_length=150, unique=True, null=True, blank=True) 
    name = models.CharField(max_length=191)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    area = models.CharField(max_length=191)
    social_status = models.CharField(max_length=100, default='غير محدد')
    image = models.ImageField(upload_to='orphans/', null=True, blank=True)
    
    guardian_name = models.CharField(max_length=191, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    contact_email = models.EmailField(max_length=191, null=True, blank=True)

    health_status = models.CharField(max_length=100, default='سليمة')
    health_details = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='orphans', null=True, blank=True)
    
    STATUS_CHOICES = [
        ('Pending', 'قيد مراجعة الإدارة'),
        ('Available', 'متاح للكفالة'),
        ('Sponsored', 'مكفول'),
    ]
    sponsorship_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.name
    
    def get_public_documents(self):
        return self.sponsor_documents.filter(is_public=True).order_by('-uploaded_at')
    

class OrphanDocument(models.Model):
    DOCUMENT_TYPES = [
        ('Legal', 'مستندات قانونية (هوية/شهادة ميلاد)'),
        ('Medical', 'تقارير طبية'),
        ('Education', 'شهادات مدرسية'),
        ('Media', 'صور وتحديثات عامة'),
        ('Other', 'أخرى'),
    ]

    orphan = models.ForeignKey(Orphan, on_delete=models.CASCADE, related_name='sponsor_documents')
    title = models.CharField(max_length=200, help_text="مثال: شهادة مدرسية - الفصل الأول")
    document = models.FileField(upload_to='orphan_docs/%Y/%m/')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='Other')
    
    # THE MASTER SWITCH: False = Admin Only, True = Sponsor can download
    is_public = models.BooleanField(default=False, help_text="تفعيل هذا الخيار سيسمح للكافل برؤية وتحميل هذا الملف")
    
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.orphan.name}"


class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='donor_profile')
    name = models.CharField(max_length=191)
    email = models.EmailField(max_length=191, unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    company = models.CharField(max_length=150, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Sponsorship(models.Model):
    SPONSORSHIP_TYPES = [
        ('Financial', 'Financial'),
        ('Educational', 'Educational'),
        ('Health', 'Health'),
        ('Monthly', 'Monthly'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
        ('Ended', 'Ended'),
    ]

    donor = models.ForeignKey(
        Donor, on_delete=models.CASCADE, related_name='sponsorships'
    )
    orphan = models.ForeignKey(
        Orphan, on_delete=models.CASCADE, related_name='sponsorships'
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    sponsorship_type = models.CharField(
        max_length=50, choices=SPONSORSHIP_TYPES, default='Financial'
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.donor.name} sponsoring {self.orphan.name}"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Credit Card', 'Credit Card'),
        ('Bank', 'Bank'),
        ('PalPay', 'PalPay'),
        ('Cash', 'Cash'),
        ('Wallet', 'Wallet'),
    ]

    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
    ]

    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Cash')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    receipt_image = models.ImageField(upload_to='receipts/%Y/%m/', null=True, blank=True)
    
    transaction_reference = models.CharField(max_length=100, null=True, blank=True) 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.sponsorship.orphan.name}"

class Document(models.Model):
    orphan = models.ForeignKey(Orphan, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(
        upload_to=orphan_document_upload_to,
        validators=[
            FileExtensionValidator(ALLOWED_DOCUMENT_EXTENSIONS),
            validate_document_file,
        ],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} for {self.orphan.name}"

class Notification(models.Model):
    SOURCE_CHOICES = [
        ('System', 'System'),
        ('Donor', 'Donor'),
    ]
    
    orphan = models.ForeignKey(Orphan, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, null=True, blank=True, related_name='donor_notifications')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='System')
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.orphan:
            return f"To Orphan: {self.orphan.name} - {self.title}"
        elif self.donor:
            return f"To Donor: {self.donor.name} - {self.title}"
        return self.title
