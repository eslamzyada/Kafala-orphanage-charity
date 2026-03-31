import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from core.utils import run_sponsorship_checkups
from .models import Orphan, Donor, Sponsorship, Payment, Notification, Guardian, OrphanDocument
from .decorators import guardian_required
import json
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import random
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse  
import requests
import os
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from .utils import send_notification



@csrf_exempt 
def kafala_ai_assistant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            api_key = os.getenv('GEMINI_API_KEY')
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

            base_instruction = """
            أنت المساعد الذكي الرسمي لمنصة "كفالة" لرعاية الأيتام. 
            أجب دائماً باللغة العربية الفصحى، بأسلوب احترافي، مباشر، ومتعاطف.
            وظيفتك إرشاد المستخدم خطوة بخطوة داخل المنصة وعدم اختراع أي معلومات غير موجودة هنا.
            """

            role_instruction = ""

            if not request.user.is_authenticated:
                role_instruction = """
                أنت تتحدث الآن مع "زائر غير مسجل".
                - هدفك: تشجيعه على التسجيل وتوضيح آلية العمل.
                - الأزرار المتاحة له: زر "تسجيل جديد" أعلى الشاشة، وزر "التبرع العام".
                - أنواع التسجيل: يمكنه التسجيل كـ "كفيل (متبرع)" أو "يتيم/وصي (مستفيد)".
                - اشرح له أن المنصة آمنة وتقتطع فقط 1% كرسوم تشغيل لضمان وصول 99% من التبرعات لليتيم.
                """
            
            elif request.user.is_superuser:
                role_instruction = """
                أنت تتحدث الآن مع "مدير النظام" (الآدمن). له الصلاحية المطلقة.
                - مسار لوحة التحكم: /admin-dashboard/
                - الأزرار والإجراءات المتاحة له في القائمة الجانبية:
                  1. "إدارة الأيتام": يمكنه رؤية الأيتام الجدد (بحالة Pending)، قراءة "مستند الوصاية" الذي رفعه الوصي، والضغط على زر "اعتماد" ليصبح اليتيم (Available).
                  2. "إدارة الكفلاء": تعديل بيانات المتبرعين.
                  3. "الكفالات": ربط وإلغاء الكفالات بين الكفيل واليتيم.
                  4. "المدفوعات": مراجعة الحوالات البنكية أو الدفع النقدي وتأكيد استلام الأموال.
                - لا تقل للمدير أبداً "ليس لديك صلاحية". وجهه دائماً للقسم المناسب في القائمة الجانبية.
                """
            
            elif Donor.objects.filter(email=request.user.email).exists():
                role_instruction = """
                أنت تتحدث الآن مع "كفيل (متبرع)".
                - مسار لوحة التحكم: /sponsor-dashboard/
                - الأزرار والإجراءات المتاحة له:
                  1. صفحة "الأيتام المتاحين": يمكنه تصفح الأيتام والضغط على زر "أكفل الآن".
                  2. صفحة "سجل المدفوعات": للقيام بدفع الكفالة.
                - آليات الدفع المتاحة له:
                  * البطاقة الائتمانية (Stripe): توضح له أن هناك رسوم تشغيل شفافة بنسبة 1% تضاف لفاتورة الدفع.
                  * حوالة بنكية / محفظة إلكترونية (PalPay) / دفع نقدي: في هذه الحالة يجب عليه رفع "صورة الإيصال" أو إدخال رقم الحوالة في النظام ليقوم المدير بمراجعتها.
                - وجه الكفيل دائماً لصفحة "سجل المدفوعات" إذا سأل عن كيفية دفع المبالغ المستحقة.
                """
            
            elif Orphan.objects.filter(username=request.user.username).exists():
                role_instruction = """
                أنت تتحدث الآن مع "وصي اليتيم".
                - مسار لوحة التحكم: /orphan-dashboard/
                - الأزرار والإجراءات المتاحة له:
                  1. صفحة "بياناتي": يجب عليه استكمال بياناته مثل "طريقة استلام الكفالة" (حوالة بنكية، محفظة إلكترونية، استلام نقدي) ورقم الحساب.
                  2. صفحة "الوثائق": يمكنه الضغط على "رفع مستند" لإضافة الشهادات المدرسية أو التقارير الطبية لليتيم ليراها الكفيل.
                - معلومة هامة جداً: إذا سأل عن سبب عدم حصوله على كفالة بعد، أخبره أن حسابه يكون مبدئياً "قيد المراجعة" (Pending) حتى تقوم إدارة المنصة بمراجعة "مستند الوصاية" الذي قام برفعه أثناء التسجيل واعتماده.
                """

            final_system_instruction = base_instruction + "\n" + role_instruction

            payload = {
                "system_instruction": {
                    "parts": [{"text": final_system_instruction}]
                },
                "contents": [
                    {"parts": [{"text": user_message}]}
                ]
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                reply_text = response_data['candidates'][0]['content']['parts'][0]['text']
                return JsonResponse({'status': 'success', 'reply': reply_text})
            else:
                print("GOOGLE API ERROR:", response_data) 
                return JsonResponse({'status': 'error', 'reply': 'عذراً، الخادم مشغول جداً حالياً.'})

        except Exception as e:
            print("DJANGO ERROR:", str(e))
            return JsonResponse({'status': 'error', 'reply': 'عذراً، حدث خطأ في الاتصال.'})
            
    return JsonResponse({'status': 'invalid_request'})
# ============= HELPER FUNCTIONS =============

def send_notification(user, title, message, link="#"):
    """دالة مركزية لإرسال الإشعارات لأي مستخدم في النظام"""
    Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        link=link
    )

def _save_document_for_orphan(orphan, uploaded_file, title, description):
    cleaned_title = (title or "").strip()
    if not cleaned_title:
        cleaned_title = "Untitled Document"
    cleaned_description = (description or "").strip()
    document = Document(
        orphan=orphan,
        title=cleaned_title[:255],
        description=cleaned_description,
        file=uploaded_file,
    )
    document.full_clean()
    document.save()
    return document

# ============= AUTH & LANDING VIEWS =============

def index(request):
    return render(request, 'landing/index.html')

def details(request):
    available_orphans = Orphan.objects.filter(sponsorships__isnull=True)[:3]
    total_sponsored = Orphan.objects.filter(sponsorships__isnull=False).distinct().count()
    total_available = Orphan.objects.filter(sponsorships__isnull=True).count()
    total_donors = User.objects.filter(is_superuser=False).count()

    context = {
        'orphans': available_orphans,
        'total_sponsored': total_sponsored,
        'total_available': total_available,
        'total_donors': total_donors,
    }
    return render(request, 'landing/details.html', context)

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username') 
        p = request.POST.get('password')
        
        print(f"DEBUG: Form submitted! Trying to log in as -> Username: '{u}'")
        
        user = authenticate(request, username=u, password=p)
        print(f"DEBUG: Did Django find this user in the database? -> {user}")
        
        if user is not None:
            login(request, user)
            print(f"DEBUG: Login successful! Checking roles for user: {user.username}")
            
            if user.is_superuser:
                return redirect('admin_dashboard') 
                
            elif hasattr(user, 'donor_profile') or Donor.objects.filter(email=user.email).exists():
                return redirect('sponsor_dashboard')
                
            elif hasattr(user, 'guardian'):
                return redirect('guardian_dashboard')
                
            elif hasattr(user, 'orphan_profile') or Orphan.objects.filter(user=user).exists():
                return redirect('orphan_dashboard')
                
            else:
                messages.error(request, "تم تسجيل الدخول، ولكن حسابك غير مسجل ككفيل، وصي، أو يتيم.")
                return redirect('index')
                
        else:
            messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة.")
            return redirect('index')
            
    return redirect('index')

def register_view(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        
        if user_type == 'sponsor':
            username = request.POST.get('sponsor_username')
            name = request.POST.get('sponsor_name')
            email = request.POST.get('sponsor_email')
            password = request.POST.get('sponsor_password')
            
            if username and email and password:
                if not User.objects.filter(username=username).exists() and not Donor.objects.filter(email=email).exists():
                    user = User.objects.create_user(username=username, email=email, password=password)
                    Donor.objects.create(name=name, email=email)
                    login(request, user)
                    return redirect('sponsor_dashboard')
                else:
                    print("Error: Username or Email already exists!")
                    return redirect('index') 

        elif user_type == 'supported':
            username = request.POST.get('guardian_username')
            password = request.POST.get('guardian_password')
            g_name = request.POST.get('guardian_name')
            g_id = request.POST.get('guardian_id')
            g_phone = request.POST.get('guardian_phone')
            g_relation = request.POST.get('guardian_relation')
            g_email = request.POST.get('guardian_email')
            legal_doc = request.FILES.get('legal_document')
            payout_method = request.POST.get('payout_method', 'Cash')
            payout_details = request.POST.get('payout_details', '')
            
            o_name = request.POST.get('orphan_name')
            o_age = request.POST.get('orphan_age')
            o_gender = request.POST.get('orphan_gender')
            o_area = request.POST.get('orphan_area')
            o_social = request.POST.get('orphan_social')
            o_health = request.POST.get('orphan_health')
            o_photo = request.FILES.get('orphan_photo')
            
            if username and password and g_name and o_name and g_email:
                if not User.objects.filter(username=username).exists():
                    
                    user = User.objects.create_user(username=username, email=g_email, password=password)    

                    guardian = Guardian.objects.create(
                        user=user,
                        name=g_name,
                        id_number=g_id,
                        phone=g_phone,
                        relation_to_orphan=g_relation,
                        legal_document=legal_doc,
                        payout_method=payout_method,
                        payout_details=payout_details,
                        is_approved=False 
                    )
                    
                    Orphan.objects.create(
                        username=username,
                        guardian=guardian,
                        name=o_name,          
                        age=o_age if o_age else None,
                        gender=o_gender,
                        area=o_area,
                        social_status=o_social,
                        health_status=o_health,
                        image=o_photo,
                        sponsorship_status='Pending'
                    )
                    
                    login(request, user)
                    return redirect('orphan_dashboard')
                else:
                    messages.error(request, "اسم المستخدم هذا مسجل مسبقاً، يرجى اختيار اسم آخر.")
                    return redirect('index')
                    
        return redirect('index')

# =================================================================
#                 GUARDIAN REGISTRATION VIEW
# =================================================================
def guardian_register(request):
    """
    Public registration flow for Guardians.
    Handles GET (render form) and POST (process registration).
    Uses transaction.atomic to ensure data integrity.
    """
    if request.user.is_authenticated:
        if hasattr(request.user, 'guardian'):
            return redirect('guardian_dashboard')
        elif request.user.is_superuser:
            return redirect('admin_dashboard')
        elif hasattr(request.user, 'donor_profile'):
            return redirect('sponsor_dashboard')
        else:
            return redirect('index')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        id_number = request.POST.get('id_number', '').strip() 
        password = request.POST.get('password', '')

        if not (name and id_number and password):
            messages.error(request, 'يرجى تعبئة جميع الحقول الإلزامية.')
            return render(request, 'landing/guardian_register.html')

        if not id_number.isdigit() or len(id_number) != 9:
            messages.error(request, 'عذراً، رقم الهوية غير صحيح. يجب أن يتكون من 9 أرقام فقط.')
            return render(request, 'landing/guardian_register.html')

        if User.objects.filter(username=id_number).exists():
            messages.error(request, 'عذراً، رقم الهوية هذا مسجل مسبقاً في النظام.')
            return render(request, 'landing/guardian_register.html')

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=id_number, password=password)
                guardian = Guardian.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    id_number=id_number, 
                    is_approved=False 
                )
            messages.success(request, 'تم تسجيل حساب الوصي بنجاح! يمكنك الآن تسجيل الدخول باستخدام رقم الهوية.')
            return redirect('index')  
        except Exception as e:
            messages.error(request, 'حدث خطأ غير متوقع أثناء التسجيل. الرجاء المحاولة مرة أخرى.')
            return render(request, 'landing/guardian_register.html')

    return render(request, 'landing/guardian_register.html')

def logout_view(request):
    logout(request)
    return redirect('index')

# ============= ADMIN DASHBOARD VIEWS =============

@login_required(login_url='index')
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    
    total_orphans = Orphan.objects.count()
    total_donors = Donor.objects.count()
    sponsored_orphans = Orphan.objects.filter(sponsorship_status='Sponsored').count()
    available_orphans = Orphan.objects.filter(sponsorship_status='Available').count()
    
    notifications = Notification.objects.order_by('-created_at')[:5]
    current_year = timezone.now().year
    
    sponsorships_this_year = Sponsorship.objects.filter(start_date__year=current_year)
    month_data = sponsorships_this_year.annotate(month=ExtractMonth('start_date')).values('month').annotate(count=Count('id'))

    monthly_counts = [0] * 12
    for entry in month_data:
        monthly_counts[entry['month'] - 1] = entry['count']

    context = {
        'total_orphans': total_orphans,
        'total_donors': total_donors,
        'sponsored_orphans': sponsored_orphans,
        'available_orphans': available_orphans,
        'notifications': notifications,
        'monthly_counts': json.dumps(monthly_counts), 
    }
    return render(request, 'Admin-dashboard/dashboard.html', context)

@login_required(login_url='index')
def manage_orphans(request):
    if not request.user.is_superuser:
        return redirect('index')
    
    pending_orphans = Orphan.objects.filter(sponsorship_status='Pending').order_by('-created_at')
    
    approved_orphans = Orphan.objects.exclude(sponsorship_status='Pending').order_by('-created_at')
    
    search_query = request.GET.get('q')
    if search_query:
        pending_orphans = pending_orphans.filter(name__icontains=search_query)
        approved_orphans = approved_orphans.filter(name__icontains=search_query)
        
    return render(request, 'Admin-dashboard/Orphanage.html', {
        'pending_orphans': pending_orphans,
        'approved_orphans': approved_orphans
    })

@login_required(login_url='index')
def approve_orphan(request, orphan_id):
    if not request.user.is_superuser:
        return redirect('index')
        
    orphan = get_object_or_404(Orphan, id=orphan_id)
    orphan.sponsorship_status = 'Available' 
    orphan.save()
    
    if hasattr(orphan, 'guardian') and orphan.guardian:
        send_notification(
            user=orphan.guardian.user,
            title="تمت الموافقة على طلبك",
            message=f"تمت مراجعة طلب تسجيل اليتيم ({orphan.name}) بنجاح وهو الآن متاح للكفالة.",
            link="/guardian/my-orphans/"
        )
        
    messages.success(request, 'تمت الموافقة بنجاح.')
    return redirect('manage_orphans')

@login_required(login_url='index')
def reject_orphan_request(request, orphan_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_orphans')
        
    orphan = get_object_or_404(Orphan, id=orphan_id)
    guardian = orphan.guardian
    
    if guardian:
        send_notification(
            user=guardian.user,
            title="رفض طلب تسجيل",
            message=f"نأسف، تم رفض طلب تسجيل اليتيم ({orphan.name}). يرجى مراجعة الإدارة.",
            link="/guardian/dashboard/"
        )
    
    orphan.delete()
    
    if guardian and guardian.orphans.count() == 0:
        user = guardian.user
        guardian.delete()
        user.delete()
        
    messages.success(request, 'تم رفض الطلب وحذفه من النظام بنجاح.')
    return redirect('manage_orphans')

@login_required(login_url='login_view')
@user_passes_test(lambda u: u.is_superuser, login_url='index')
def add_orphan(request):
    if request.method == 'POST':
        username = request.POST.get('username') 
        name = request.POST.get('name') 
        password = request.POST.get('password') 
        
        guardian_choice = request.POST.get('guardian_choice')
        new_g_username = request.POST.get('new_g_username')
        new_g_password = request.POST.get('new_g_password')

        if guardian_choice == 'new' and username == new_g_username:
            messages.error(request, "خطأ: لا يمكن استخدام نفس اسم المستخدم لليتيم والوصي.")
            return redirect('add_orphan') 

        if User.objects.filter(username=username).exists():
            messages.error(request, f"خطأ: اسم المستخدم لليتيم ({username}) محجوز مسبقاً.")
            return redirect('add_orphan')

        if guardian_choice == 'new' and User.objects.filter(username=new_g_username).exists():
            messages.error(request, f"خطأ: اسم المستخدم للوصي ({new_g_username}) محجوز مسبقاً.")
            return redirect('add_orphan')

        try:
            with transaction.atomic():
                guardian = None

                if guardian_choice == 'existing':
                    guardian_id = request.POST.get('guardian_id')
                    guardian = Guardian.objects.get(id=guardian_id)
                        
                elif guardian_choice == 'new':
                    g_user = User.objects.create_user(username=new_g_username, password=new_g_password)
                    guardian = Guardian.objects.create(
                        user=g_user, 
                        name=request.POST.get('new_g_name'), 
                        phone=request.POST.get('new_g_phone')
                    )

                orphan_user = User.objects.create_user(username=username, password=password)
                
                orphan = Orphan.objects.create(
                    user=orphan_user,   
                    username=username, 
                    name=name,         
                    age=request.POST.get('age'),
                    gender=request.POST.get('gender'),
                    area=request.POST.get('area'),
                    health_status=request.POST.get('health_status'),
                    social_status=request.POST.get('social_status'),
                    guardian=guardian,    
                    sponsorship_status='Pending'
                )
                
                if 'image' in request.FILES:
                    orphan.image = request.FILES['image']
                    orphan.save()
                    admins = User.objects.filter(is_superuser=True)
                    for admin in admins:
                        send_notification(
                            user=admin,
                            title="طلب كفالة يتيم جديد 👶",
                            message=f"قام الوصي بتسجيل يتيم جديد باسم ({orphan.name}) وهو بانتظار المراجعة والموافقة.",
                            link=f"/admin-orphan-details/{orphan.id}/" 
                        )
                    
                if 'document' in request.FILES:
                    try:
                        _save_document_for_orphan(
                            orphan,
                            request.FILES['document'],
                            "Initial Document",
                            "",
                        )
                    except ValidationError:
                        pass
                
                messages.success(request, "تمت إضافة اليتيم والوصي بنجاح! يمكن لليتيم تسجيل الدخول الآن.")
                return redirect('manage_orphans')

        except Exception as e:
            messages.error(request, "حدث خطأ غير متوقع أثناء الحفظ. يرجى المحاولة مرة أخرى.")
            return redirect('add_orphan')
            
    guardians = Guardian.objects.all()
    return render(request, 'Admin-dashboard/newOrphan.html', {'guardians': guardians})

@login_required(login_url='index')
def admin_orphan_details(request, orphan_id):
    if not request.user.is_superuser:
        return redirect('index')
    
    orphan = get_object_or_404(Orphan, id=orphan_id)
    guardian = orphan.guardian 
    
    documents = orphan.sponsor_documents.all().order_by('-uploaded_at')
    sponsorships = orphan.sponsorships.all()
    
    if request.method == 'POST':
        
        if 'edit_orphan' in request.POST:
            # 🌟 تحديث البيانات الأساسية
            orphan.name = request.POST.get('name', orphan.name)
            orphan.age = request.POST.get('age', orphan.age)
            orphan.area = request.POST.get('area', orphan.area)
            orphan.social_status = request.POST.get('social_status', orphan.social_status)
            orphan.health_status = request.POST.get('health_status', orphan.health_status)
            
            # 🌟 تحديث بيانات الكفالة والقصة
            orphan.sponsorship_status = request.POST.get('sponsorship_status', orphan.sponsorship_status)
            orphan.sponsorship_need = request.POST.get('sponsorship_need', orphan.sponsorship_need)
            orphan.story = request.POST.get('story', orphan.story)
            orphan.kinship_to_guardian = request.POST.get('kinship_to_guardian', orphan.kinship_to_guardian)
            
            requested_amount = request.POST.get('requested_amount')
            if requested_amount:
                orphan.requested_amount = int(requested_amount)
            
            # 🌟 تحديث الملفات والمستندات الجديدة
            if 'birth_certificate' in request.FILES:
                orphan.birth_certificate = request.FILES['birth_certificate']
            if 'death_certificate' in request.FILES:
                orphan.death_certificate = request.FILES['death_certificate']
            if 'guardianship_document' in request.FILES:
                orphan.guardianship_document = request.FILES['guardianship_document']
            if 'health_report' in request.FILES:
                orphan.health_report = request.FILES['health_report']
                
            orphan.save()

            # 🌟 تحديث بيانات الوصي
            if guardian:
                guardian.name = request.POST.get('guardian_name', guardian.name)
                guardian.id_number = request.POST.get('guardian_id', guardian.id_number)
                guardian.phone = request.POST.get('guardian_phone', guardian.phone)
                guardian.payout_method = request.POST.get('payout_method', guardian.payout_method)
                guardian.payout_details = request.POST.get('payout_details', guardian.payout_details)
                
                new_email = request.POST.get('guardian_email')
                if new_email and guardian.user:
                    guardian.user.email = new_email
                    guardian.user.save()
                
                if 'id_document' in request.FILES:
                    guardian.id_document = request.FILES['id_document']
                guardian.save()
                
            messages.success(request, 'تم تحديث بيانات اليتيم والوصي بنجاح.')
            return redirect('admin_orphan_details', orphan_id=orphan.id)

        elif 'upload_document' in request.POST:
            doc_title = request.POST.get('title')
            doc_file = request.FILES.get('document')
            is_public = request.POST.get('is_public') == 'on' 
            
            if doc_title and doc_file:
                OrphanDocument.objects.create(
                    orphan=orphan,
                    title=doc_title,
                    document=doc_file,
                    document_type='Other',
                    is_public=is_public 
                )
                messages.success(request, 'تم رفع الوثيقة الإضافية بنجاح.')
            else:
                messages.error(request, 'حدث خطأ. يرجى التأكد من إرفاق الملف وكتابة العنوان.')
                
            return redirect('admin_orphan_details', orphan_id=orphan.id)

        elif 'toggle_core_doc' in request.POST:
            doc_type = request.POST.get('toggle_core_doc')
            
            if doc_type == 'birth':
                orphan.is_birth_cert_public = not orphan.is_birth_cert_public
                orphan.save()
            elif doc_type == 'death':
                orphan.is_death_cert_public = not orphan.is_death_cert_public
                orphan.save()
            elif doc_type == 'guardian_id' and guardian:
                guardian.is_id_public = not guardian.is_id_public
                guardian.save()
                
            messages.success(request, 'تم تحديث حالة ظهور الوثيقة للكافل بنجاح.')
            return redirect('admin_orphan_details', orphan_id=orphan.id)

    context = {
        'orphan': orphan,
        'guardian': guardian,
        'documents': documents, 
        'sponsorships': sponsorships
    }
    return render(request, 'Admin-dashboard/showOrphan.html', context)

@login_required(login_url='index')
def delete_orphan(request, orphan_id):
    if not request.user.is_superuser:
        return redirect('index')
    if request.method != 'POST':
        return redirect('manage_orphans')
    
    orphan = get_object_or_404(Orphan, id=orphan_id)
    orphan.delete()
    return redirect('manage_orphans')

@login_required(login_url='index')
def manage_donors(request):
    if not request.user.is_superuser:
        return redirect('index')
    donors = Donor.objects.all().order_by('-created_at')
    return render(request, 'Admin-dashboard/DonorsManagement.html', {'donors': donors})

@login_required(login_url='index')
def add_donor(request):
    if not request.user.is_superuser:
        return redirect('index')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '')
        create_login = request.POST.get('create_login') == 'on'  
        
        if not name:
            return render(request, 'Admin-dashboard/newDonor.html', {'error': 'Donor name is required'})
        if email and User.objects.filter(email=email).exists():
            return render(request, 'Admin-dashboard/newDonor.html', {'error': 'This email is already registered in the system'})
        if email and Donor.objects.filter(email=email).exists():
            return render(request, 'Admin-dashboard/newDonor.html', {'error': 'This email is already registered as a donor'})
        
        if create_login and email:
            try:
                User.objects.create_user(
                    username=email.split('@')[0],  
                    email=email,
                    password='DefaultPassword123!'  
                )
            except Exception as e:
                return render(request, 'Admin-dashboard/newDonor.html', {'error': f'Could not create user account: {str(e)}'})
        
        Donor.objects.create(name=name, email=email, phone=phone)
        return redirect('manage_donors')
        
    return render(request, 'Admin-dashboard/newDonor.html')

@login_required(login_url='index')
def edit_donor(request, donor_id):
    if not request.user.is_superuser:
        return redirect('index')
    donor = get_object_or_404(Donor, id=donor_id)
    if request.method == 'POST':
        donor.name = request.POST.get('name')
        donor.email = request.POST.get('email')
        donor.phone = request.POST.get('phone', '')
        donor.save()
        return redirect('manage_donors')
    return render(request, 'Admin-dashboard/editDonor.html', {'donor': donor})

@login_required(login_url='index')
def delete_donor(request, donor_id):
    if not request.user.is_superuser:
        return redirect('index')
    if request.method != 'POST':
        return redirect('manage_donors')
    
    donor = get_object_or_404(Donor, id=donor_id)
    donor.delete() 
    return redirect('manage_donors')

@login_required(login_url='index')
def manage_sponsorships(request):
    if not request.user.is_superuser:
        return redirect('index')
    sponsorships = Sponsorship.objects.select_related('donor', 'orphan').all().order_by('-created_at')
    return render(request, 'Admin-dashboard/GuaranteeManagement.html', {'sponsorships': sponsorships})

@login_required(login_url='index')
def manage_payments(request):
    if not request.user.is_superuser:
        return redirect('index')
        
    if request.method == 'POST' and 'confirm_cash' in request.POST:
        payment_id = request.POST.get('payment_id')
        entered_code = request.POST.get('reference_code', '').strip()
        payment = get_object_or_404(Payment, id=payment_id)
        
        if payment.payment_method == 'Cash' and payment.status == 'Pending':
            if entered_code == payment.transaction_reference:
                try:
                    with transaction.atomic():
                        payment.status = 'Completed'
                        payment.save()
                        
                        sponsorship = payment.sponsorship
                        sponsorship.status = 'Active'
                        sponsorship.save()
                        
                        orphan = sponsorship.orphan
                        orphan.sponsorship_status = 'Sponsored'
                        orphan.save()
                        
                    messages.success(request, 'تم تأكيد الدفع النقدي وتفعيل الكفالة وتحديث حالة اليتيم بنجاح.')
                except Exception as e:
                    messages.error(request, 'حدث خطأ غير متوقع أثناء معالجة البيانات.')
            else:
                messages.error(request, 'الكود المرجعي غير صحيح. يرجى التأكد من الكود مع الكافل.')
        return redirect('manage_payments')

    payments = Payment.objects.select_related('sponsorship__donor', 'sponsorship__orphan').all().order_by('-created_at')
    return render(request, 'Admin-dashboard/paymentsManagement.html', {'payments': payments})

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required(login_url='index')
def create_stripe_checkout_session(request, payment_id):
    try:
        donor = Donor.objects.get(email=request.user.email)
        payment = get_object_or_404(Payment, id=payment_id, sponsorship__donor=donor)
        
        donation_amount_cents = int(payment.amount * 100)
        platform_fee_cents = int(donation_amount_cents * 0.01) 
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'كفالة اليتيم: {payment.sponsorship.orphan.name}',
                            'description': 'المبلغ الصافي الذي يصل لليتيم بالكامل',
                        },
                        'unit_amount': donation_amount_cents,
                    },
                    'quantity': 1,
                },
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'رسوم تشغيل المنصة (1%)',
                            'description': 'مساهمة لتغطية تكاليف الخوادم وبوابات الدفع الإلكتروني',
                        },
                        'unit_amount': platform_fee_cents,
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            client_reference_id=str(payment.pk), 
            success_url=request.build_absolute_uri(reverse('donor_payments')) + '?success=true',
            cancel_url=request.build_absolute_uri(reverse('pay_checkout', args=[payment.pk])) + '?canceled=true',
        )
        
        if checkout_session.url:
            return redirect(checkout_session.url)
        else:
            messages.error(request, "لم نتمكن من إنشاء جلسة الدفع، يرجى المحاولة مرة أخرى.")
            return redirect('donor_payments')
            
    except Exception as e:
        print(f"STRIPE ERROR: {str(e)}")
        messages.error(request, "حدث خطأ أثناء الاتصال ببوابة الدفع. يرجى المحاولة لاحقاً.")
        return redirect('donor_payments')
    
@login_required
def donor_dashboard(request):
    donor = get_object_or_404(Donor, user=request.user)
    
    try:
        run_sponsorship_checkups(request.user)
    except Exception as e:
        print(f"Error in background check: {e}")

    sponsored_count = Sponsorship.objects.filter(donor=donor, status='Active').count()
    available_count = Orphan.objects.filter(sponsorship_status='Available').count()
    
    context = {
        'donor': donor,
        'sponsored_count': sponsored_count,
        'available_count': available_count,
    }
    return render(request, 'Donor-dashboard/dashboard.html', context)

@login_required
def approve_sponsorship(request, sponsorship_id):
    """دالة موافقة الأدمن على طلب الكفالة"""
    if not request.user.is_superuser:
        return redirect('index')
    
    sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
    sponsorship.status = 'Active'
    sponsorship.save()
    
    orphan = sponsorship.orphan
    orphan.sponsorship_status = 'Sponsored'
    orphan.save()
    
    send_notification(
        user=sponsorship.donor.user,
        title="مبارك! تمت الموافقة على الكفالة",
        message=f"تمت الموافقة على كفالتك لليتيم ({orphan.name}). شكراً لعطائك.",
        link="/donor/my-sponsorships/"
    )
    
    messages.success(request, "تم تفعيل الكفالة بنجاح.")
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def reject_sponsorship(request, sponsorship_id):
    if not request.user.is_superuser:
        return redirect('index')
        
    if request.method == 'POST':
        sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
        
        try:
            with transaction.atomic():
                sponsorship.status = 'Canceled'
                sponsorship.save()
                
                orphan = sponsorship.orphan
                if orphan.sponsorship_status != 'Available':
                    orphan.sponsorship_status = 'Available'
                    orphan.save()
                
                Payment.objects.filter(sponsorship=sponsorship, status='Pending').update(status='Failed')
                
            messages.success(request, 'تم رفض الكفالة، وإلغاء المدفوعات المعلقة، وتحرير اليتيم بنجاح.')
        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء رفض الكفالة.')
            
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def notifications_view(request):
    if not request.user.is_superuser:
        return redirect('index')
        
    notifications = Notification.objects.filter(Q(recipient__isnull=True) | Q(recipient=request.user)).order_by('-created_at')
    
    return render(request, 'Admin-dashboard/notifications.html', {
        'notifications': notifications,
    })

@login_required(login_url='index')
def edit_profile(request):
    if not request.user.is_superuser:
        return redirect('index')
    
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('firstName', user.first_name)
        user.last_name = request.POST.get('lastName', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        return redirect('edit_profile')
        
    return render(request, 'Admin-dashboard/editProfile.html')

@login_required(login_url='index')
def accept_sponsorship(request, sponsorship_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
        
    sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
    
    from django.db import transaction
    with transaction.atomic():
        sponsorship.status = 'Active'
        sponsorship.save()
        
        orphan = sponsorship.orphan
        orphan.sponsorship_status = 'Sponsored'
        orphan.save()
        
        Payment.objects.filter(sponsorship=sponsorship, status='Pending').update(status='Completed')
        
    messages.success(request, 'تم قبول الكفالة بنجاح وتحديث حالة اليتيم إلى (مكفول).')
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def end_sponsorship(request, sponsorship_id):
    if not request.user.is_superuser:
        return redirect('index')
        
    if request.method == 'POST':
        sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
        
        with transaction.atomic():
            sponsorship.status = 'Ended'
            sponsorship.save()
            
            orphan = sponsorship.orphan
            orphan.sponsorship_status = 'Available'
            orphan.save()
            
            Payment.objects.filter(sponsorship=sponsorship, status='Pending').update(status='Failed')
            
        messages.success(request, 'تم إنهاء الكفالة بنجاح.')
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def renew_sponsorship(request, spon_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
    
    spon = get_object_or_404(Sponsorship, id=spon_id)
    spon.status = 'Active'
    spon.save() 
    
    spon.orphan.sponsorship_status = 'Sponsored'
    spon.orphan.save()
    
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def delete_sponsorship(request, sponsorship_id):
    if not request.user.is_superuser:
        return redirect('index')
        
    if request.method == 'POST':
        sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
        
        with transaction.atomic():
            orphan = sponsorship.orphan
            orphan.sponsorship_status = 'Available'
            orphan.save()
            
            sponsorship.delete()
            
        messages.success(request, 'تم حذف الكفالة وسجلاتها بنجاح.')
    return redirect('manage_sponsorships')


# ============= ORPHAN DASHBOARD VIEWS =============

@login_required(login_url='index')
def orphan_dashboard(request):
    try:
        orphan = Orphan.objects.get(user=request.user)
        sponsorship = Sponsorship.objects.filter(orphan=orphan, status='Active').first()
    except Orphan.DoesNotExist:
        messages.error(request, 'عذراً، لا يوجد ملف يتيم مرتبط بهذا الحساب.')
        return redirect('index')

    context = {
        'orphan': orphan, 
        'sponsorship': sponsorship, 
    }
    return render(request, 'Orphan-dashboard/dashboard.html', context)

@login_required(login_url='index')
def orphan_profile(request):
    orphan = get_object_or_404(Orphan, user=request.user)
    guardian = orphan.guardian 
    
    context = {
        'orphan': orphan,
        'guardian': guardian,
    }
    return render(request, 'Orphan-dashboard/detailesOrphan.html', context)


@login_required(login_url='index')
def orphan_sponsorships(request):
    orphan = get_object_or_404(Orphan, user=request.user)
    
    sponsorships = Sponsorship.objects.filter(orphan=orphan).order_by('-start_date')

    context = {
        'orphan': orphan,
        'sponsorships': sponsorships
    }
    return render(request, 'Orphan-dashboard/Myguarantee.html', context)

@login_required(login_url='index')
def orphan_notifications(request):
    orphan = get_object_or_404(Orphan, user=request.user)
    
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        
    return render(request, 'Orphan-dashboard/notifications.html', {
        'orphan': orphan, 
        'notifications': all_notifications 
    })

@login_required(login_url='index')
def orphan_edit_profile(request):
    orphan = get_object_or_404(Orphan, user=request.user)
    
    if request.method == 'POST':
        orphan.age = request.POST.get('age', orphan.age)
        orphan.gender = request.POST.get('gender', orphan.gender)
        orphan.health_status = request.POST.get('health_status', orphan.health_status)
        orphan.area = request.POST.get('area', orphan.area)
        orphan.social_status = request.POST.get('social_status', orphan.social_status)
        
        if 'profile_image' in request.FILES:
            orphan.image = request.FILES['profile_image']
            
        orphan.save()
        messages.success(request, 'تم حفظ التعديلات الشخصية بنجاح.')
        return redirect('orphan_edit_profile') 

    context = {
        'orphan': orphan,
        'is_male': orphan.gender == 'Male',
        'is_female': orphan.gender == 'Female',
    }
    return render(request, 'Orphan-dashboard/editProfile.html', context)

# =================================================================
#                     NOTIFICATIONS VIEWS
# =================================================================

@login_required(login_url='index')
def mark_notification_read(request, notif_id):
    """تحديد إشعار واحد كمقروء"""
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notification.is_read = True
        notification.save()
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required(login_url='index')
def mark_all_notifications_read(request):
    """تحديد كل الإشعارات كمقروءة"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required(login_url='index')
def delete_notification(request, notif_id):
    """حذف الإشعار نهائياً"""
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notification.delete()
        messages.success(request, 'تم حذف الإشعار بنجاح.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))

# =================================================================
#                     SPONSOR / DONOR DASHBOARD VIEWS
# =================================================================

@login_required(login_url='index')
def sponsor_dashboard(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        
        sponsored_count = Sponsorship.objects.filter(donor=donor, status='Active').count()
        available_count = Orphan.objects.filter(sponsorship_status='Available').exclude(sponsorships__donor=donor).distinct().count()
    except Donor.DoesNotExist:
        donor = None
        unread_count = 0
        recent_notifications = []
        sponsored_count = 0
        available_count = Orphan.objects.filter(sponsorship_status='Available').count()
        
    context = {
        'donor': donor,
        'sponsored_count': sponsored_count,
        'available_count': available_count,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/dashboard.html', context)


@login_required(login_url='index')
def donor_sponsorships(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        sponsorships = Sponsorship.objects.filter(donor=donor).select_related('orphan')
        # donor_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        # unread_count = donor_notifications.filter(is_read=False).count()
        # recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        donor = None
        sponsorships = []
        unread_count = 0
        recent_notifications = []
        
    context = {
        'donor': donor,
        'sponsorships': sponsorships,
        # 'unread_count': unread_count,
        # 'recent_notifications': recent_notifications,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/guarantee.html', context)


@login_required(login_url='index')
def create_new_sponsorship(request, orphan_id):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(email=request.user.email)
            orphan = get_object_or_404(Orphan, id=orphan_id)
            
            if orphan.sponsorship_status != 'Available':
                messages.error(request, "عذراً، هذا اليتيم غير متاح للكفالة في الوقت الحالي.")
                return redirect('donor_orphans')

            sponsorship_type = orphan.sponsorship_need
            
            if orphan.requested_amount:
                base_amount = float(orphan.requested_amount)
            else:
                if sponsorship_type == 'Educational':
                    base_amount = 40.00
                elif sponsorship_type == 'Health':
                    base_amount = 60.00
                elif sponsorship_type == 'Monthly':
                    base_amount = 60.00
                else:
                    base_amount = 50.00
            
            duration_months = int(request.POST.get('duration_months', 1))
            total_amount = base_amount * duration_months

            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=30 * duration_months)

            sponsorship = Sponsorship.objects.create(
                donor=donor,
                orphan=orphan,
                amount=total_amount, 
                start_date=start_date,
                end_date=end_date,    
                status='Pending',
                sponsorship_type=sponsorship_type 
            )
            orphan.sponsorship_status = 'Pending'
            orphan.save()
                        
            return redirect('pay_checkout', sponsorship_id=sponsorship.id)
            
        except Donor.DoesNotExist:
            return redirect('sponsor_dashboard')
        except ValueError:
            messages.error(request, "يرجى التأكد من إدخال بيانات صحيحة للمدة.")
            return redirect('donor_orphans')
            
    return redirect('donor_orphans')


@login_required(login_url='index')
def donor_orphans(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        available_orphans = Orphan.objects.filter(
            sponsorship_status='Available'
        ).exclude(
            sponsorships__donor=donor,
            sponsorships__status__in=['Active', 'Pending']
        ).distinct()
        
    except Donor.DoesNotExist:
        donor = None
        available_orphans = Orphan.objects.filter(sponsorship_status='Available')
        
    query = request.GET.get('q')
    if query:
        available_orphans = available_orphans.filter(name__icontains=query)
        
    context = {
        'donor': donor,
        'orphans': available_orphans,
        'user': request.user,
        'search_query': query
    }
    return render(request, 'Donor-dashboard/showOrphan.html', context)

@login_required(login_url='index')
def donor_notifications(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        recent_notifications = notifications[:5]
    except Donor.DoesNotExist:
        donor = None
        notifications = []
        unread_count = 0
        recent_notifications = []
        
    context = {
        'donor': donor,
        'notifications': notifications,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/notifications.html', context)


@login_required(login_url='index')
def donor_edit_profile(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        # donor_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        # unread_count = donor_notifications.filter(is_read=False).count()
        # recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        return redirect('sponsor_dashboard')
        
    if request.method == 'POST':
        new_email = request.POST.get('email')
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            request.user.username = new_email 
            request.user.save()
            donor.email = new_email 

        new_name = request.POST.get('name')
        if new_name:
            donor.name = new_name
            request.user.first_name = new_name
            request.user.save()
            
        donor.phone = request.POST.get('phone', donor.phone)
        donor.company = request.POST.get('company', donor.company)
        donor.address = request.POST.get('address', donor.address)
        
        if 'profile_image' in request.FILES:
            donor.image = request.FILES['profile_image']

        donor.save()
        return redirect('donor_edit_profile')
    
    context = {
        'donor': donor,
        # 'unread_count': unread_count,
        # 'recent_notifications': recent_notifications,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/editProfile.html', context)

@login_required(login_url='index')
def mark_donor_notification_read(request, notif_id):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(email=request.user.email)
            notif = Notification.objects.get(id=notif_id, donor=donor)
            notif.is_read = True
            notif.save()
            return JsonResponse({'status': 'success'})
        except (Donor.DoesNotExist, Notification.DoesNotExist):
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)

@login_required(login_url='index')
def mark_all_donor_notifications_read(request):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(email=request.user.email)
            Notification.objects.filter(donor=donor, is_read=False).update(is_read=True)
            return JsonResponse({'status': 'success'})
        except Donor.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)

@login_required(login_url='index')
def send_payment_reminder(request, payment_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_payments')
    
    payment = get_object_or_404(Payment, id=payment_id)
    donor = payment.sponsorship.donor
    
    Notification.objects.create(
        donor=donor,
        title="تذكير بدفع الكفالة",
        message=f"عزيزي الكافل، نود تذكيركم بوجود دفعة قيد الانتظار بقيمة ${payment.amount} لكفالة اليتيم {payment.sponsorship.orphan.name}. يرجى استكمال الدفع.",
        source="النظام",
        is_read=False
    )
    
    return redirect('manage_payments')

@login_required(login_url='index')
def mark_admin_notif_read(request, notif_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('notifications')
    
    notif = get_object_or_404(Notification, id=notif_id)
    notif.is_read = True
    notif.save()
    return redirect('notifications')

@login_required(login_url='index')
def delete_admin_notif(request, notif_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('notifications')
    
    notif = get_object_or_404(Notification, id=notif_id)
    notif.delete()
    return redirect('notifications')

@login_required(login_url='index')
def donor_payments(request):
    try:
        donor = Donor.objects.get(email=request.user.email)

        Payment.objects.filter(
            sponsorship__donor=donor, 
            status='Pending', 
            sponsorship__status__in=['Canceled', 'Ended', 'Rejected']
        ).update(status='Failed')
        
        payments = Payment.objects.filter(sponsorship__donor=donor).order_by('-id')
        
    except Donor.DoesNotExist:
        donor = None
        payments = []
        
    context = {
        'donor': donor,
        'payments': payments,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/payments.html', context)

@login_required(login_url='index')
def pay_checkout(request, sponsorship_id):
    try:
        donor = Donor.objects.get(email=request.user.email)
        sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id, donor=donor)
    except Donor.DoesNotExist:
        return redirect('sponsor_dashboard')

    if request.method == 'POST':
        method = request.POST.get('payment_method')
        reference = request.POST.get('transaction_reference', '')
        
        payment = Payment.objects.create(
            sponsorship=sponsorship,
            amount=sponsorship.amount,
            payment_date=timezone.now().date(),
            status='Pending',
            payment_method=method
        )
        
        if method == 'Credit Card':
            return redirect('create_stripe_checkout_session', payment_id=payment.id)
            
        elif method in ['Bank', 'PalPay']:
            if 'receipt_image' in request.FILES:
                payment.receipt_image = request.FILES['receipt_image']
            payment.transaction_reference = reference
            payment.save()
            messages.success(request, 'تم رفع إيصال الدفع. يرجى الانتظار لحين تأكيد الإدارة.')
            
        elif method == 'Cash':
            payment.transaction_reference = f"CASH-{payment.id}-{random.randint(1000, 9999)}"
            payment.save()
            messages.success(request, f'تم تسجيل طلب دفع نقدي. كود المراجعة لتسليمه للإدارة هو: {payment.transaction_reference}')
            
        return redirect('donor_payments')

    context = {
        'donor': donor,
        'sponsorship': sponsorship, 
        'user': request.user
    }
    return render(request, 'Donor-dashboard/checkout.html', context)

@login_required(login_url='index')
def initiate_sponsorship_payment(request, spon_id):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(email=request.user.email)
            sponsorship = get_object_or_404(Sponsorship, id=spon_id, donor=donor)
            
            new_payment = Payment.objects.create(
                sponsorship=sponsorship,
                amount=sponsorship.amount,
                payment_date=timezone.now().date(),
                status='Pending',
                payment_method='Cash' 
            )
            
            return redirect('pay_checkout', payment_id=new_payment.id)
            
        except Donor.DoesNotExist:
            return redirect('sponsor_dashboard')
            
    return redirect('donor_sponsorships')


@guardian_required
def guardian_dashboard(request):
    """
    Guardian home page showing summary statistics and recent activity.
    
    SECURITY: @guardian_required ensures only authenticated users with
    a Guardian profile can access this view. All QuerySets are scoped
    to request.user.guardian to enforce strict data isolation.
    """
    guardian = request.user.guardian
    
    my_orphans = Orphan.objects.filter(guardian=guardian)
    
    total_orphans = my_orphans.count()
    pending_count = my_orphans.filter(sponsorship_status='Pending').count()
    available_count = my_orphans.filter(sponsorship_status='Available').count()
    sponsored_count = my_orphans.filter(sponsorship_status='Sponsored').count()
    
    recent_documents = OrphanDocument.objects.filter(
        orphan__guardian=guardian
    ).select_related('orphan').order_by('-uploaded_at')[:5]
    
    context = {
        'guardian': guardian,
        'total_orphans': total_orphans,
        'pending_count': pending_count,
        'available_count': available_count,
        'sponsored_count': sponsored_count,
        'recent_documents': recent_documents,
    }
    return render(request, 'Guardian-dashboard/dashboard.html', context)


@guardian_required
def guardian_my_orphans(request):
    """
    List view of all orphans linked to this guardian.
    
    WHY select_related is NOT used here: Orphan does not have deep FK
    chains we need for this view — guardian is already known.
    """
    guardian = request.user.guardian
    orphans = Orphan.objects.filter(guardian=guardian).order_by('-created_at')
    
    context = {
        'guardian': guardian,
        'orphans': orphans,
    }
    return render(request, 'Guardian-dashboard/guardian_my_orphans.html', context)


@guardian_required
def guardian_upload_document(request, orphan_id):
    """
    Upload an OrphanDocument for a specific orphan.
    
    CRITICAL SECURITY — IDOR PROTECTION:
    We do NOT use get_object_or_404(Orphan, id=orphan_id) alone because that
    would let a guardian manipulate the URL to access another guardian's orphan.
    Instead, we filter by BOTH orphan_id AND guardian to ensure ownership.
    """
    guardian = request.user.guardian
    
    orphan = Orphan.objects.filter(id=orphan_id, guardian=guardian).first()
    if not orphan:
        messages.error(request, "ليس لديك صلاحية الوصول لبيانات هذا اليتيم.")
        return redirect('guardian_my_orphans')
    
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document_file')
        title = request.POST.get('title', '').strip()
        doc_type = request.POST.get('document_type', 'Other')
        
        if not uploaded_file:
            messages.error(request, "يرجى اختيار ملف للرفع.")
        elif not title:
            messages.error(request, "يرجى إدخال عنوان للمستند.")
        else:
            try:
                with transaction.atomic():
                    OrphanDocument.objects.create(
                        orphan=orphan,
                        title=title[:200],
                        document=uploaded_file,
                        document_type=doc_type,
                        is_public=False,  
                    )
                messages.success(request, f"تم رفع المستند '{title}' بنجاح لليتيم {orphan.name}.")
                return redirect('guardian_my_orphans')
            except Exception:
                messages.error(request, "حدث خطأ أثناء رفع الملف. يرجى المحاولة مرة أخرى.")
    
    context = {
        'guardian': guardian,
        'orphan': orphan,
        'document_types': OrphanDocument.DOCUMENT_TYPES,
    }
    return render(request, 'Guardian-dashboard/upload_document.html', context)


@guardian_required
def guardian_apply_orphan(request):
    guardian = request.user.guardian
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        area = request.POST.get('area', '').strip()
        social_status = request.POST.get('social_status', 'غير محدد').strip()
        health_status = request.POST.get('health_status', 'ممتازة').strip()
        
        orphan_username = request.POST.get('orphan_username', '').strip()
        orphan_password = request.POST.get('orphan_password', '')
        story = request.POST.get('story', '').strip()
        kinship = request.POST.get('kinship_to_guardian', '').strip()
        
        birth_cert = request.FILES.get('birth_certificate')
        death_cert = request.FILES.get('death_certificate')
        guardianship_cert = request.FILES.get('guardianship_document')
        sponsorship_need = request.POST.get('sponsorship_need', 'Monthly')
        requested_amount = request.POST.get('requested_amount', '').strip()
        health_report = request.FILES.get('health_report')
        
        if not name or not orphan_username or not orphan_password or not birth_cert or not death_cert:
            messages.error(request, "يرجى تعبئة جميع الحقول الأساسية وإرفاق المستندات الإلزامية (شهادة الميلاد والوفاة).")
            return render(request, 'Guardian-dashboard/apply.html', {'guardian': guardian})
            
        if User.objects.filter(username=orphan_username).exists():
            messages.error(request, f"عذراً، رقم الهوية / اسم المستخدم '{orphan_username}' مسجل مسبقاً.")
            return render(request, 'Guardian-dashboard/apply.html', {'guardian': guardian})
        
        if (health_status in ['مريض', 'ذوي احتياجات خاصة'] or sponsorship_need == 'Health') and not health_report:
            messages.error(request, "التقرير الطبي إلزامي للحالات المرضية، أو ذوي الاحتياجات الخاصة، أو عند طلب كفالة صحية.")
            return render(request, 'Guardian-dashboard/apply.html', {'guardian': guardian})
        
        try:
            with transaction.atomic():
                orphan_user = User.objects.create_user(username=orphan_username, password=orphan_password)
                
                orphan = Orphan.objects.create(
                    user=orphan_user,    
                    guardian=guardian,      
                    name=name,
                    age=int(age) if age else None,
                    gender=gender,
                    area=area,
                    social_status=social_status,
                    health_status=health_status,
                    story=story, 
                    kinship_to_guardian=kinship,
                    birth_certificate=birth_cert, 
                    death_certificate=death_cert, 
                    guardianship_document=guardianship_cert,
                    sponsorship_need=sponsorship_need,
                    requested_amount=int(requested_amount) if requested_amount else None,
                    health_report=health_report, 
                    sponsorship_status='Pending',
                )
                
                if 'image' in request.FILES:
                    orphan.image = request.FILES['image']
                    orphan.save()
                
                admins = User.objects.filter(is_superuser=True)
                for admin in admins:
                    Notification.objects.create(
                        recipient=admin,
                        title="طلب تسجيل يتيم جديد",
                        message=f"قام الوصي ({guardian.name}) بتقديم طلب لليتيم '{orphan.name}'. يرجى مراجعة المستندات.",
                        link=f"/admin/core/orphan/{orphan.id}/change/"
                    )
                
            messages.success(request, f"تم تقديم طلب اليتيم '{name}' بنجاح، وتم إشعار الإدارة. الطلب قيد المراجعة.")
            return redirect('guardian_my_orphans')
            
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            messages.error(request, "حدث خطأ أثناء رفع المستندات والتسجيل. يرجى المحاولة مرة أخرى.")
            return render(request, 'Guardian-dashboard/apply.html', {'guardian': guardian}) 
    
    return render(request, 'Guardian-dashboard/apply.html', {'guardian': guardian})

@login_required(login_url='index')
def guardian_profile(request):
    try:
        guardian = request.user.guardian
    except:
        return redirect('index') 

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()

        guardian.phone = request.POST.get('phone', guardian.phone)
        guardian.payout_method = request.POST.get('payout_method', guardian.payout_method)
        guardian.payout_details = request.POST.get('payout_details', guardian.payout_details)
        guardian.save()

        messages.success(request, 'تم حفظ تعديلات حسابك بنجاح.')
        return redirect('guardian_profile')

    context = {
        'guardian': guardian,
    }
    return render(request, 'Guardian-dashboard/editProfile.html', context)

@login_required(login_url='index')
def guardian_notifications(request):
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    context = {
        'notifications': all_notifications 
    }
    return render(request, 'Guardian-dashboard/notifications.html', context)

# =================================================================
#                     ADMIN MANAGE GUARDIANS
# =================================================================
@login_required(login_url='index')
@user_passes_test(lambda u: u.is_superuser)
def manage_guardians(request):
    if not request.user.is_superuser:
        return redirect('index')

    guardians = Guardian.objects.all().order_by('-id')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name')
            id_number = request.POST.get('id_number') 
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            password = request.POST.get('password') 
            payout_method = request.POST.get('payout_method')
            payout_details = request.POST.get('payout_details')

            id_document = request.FILES.get('id_document')

            from django.contrib.auth.models import User
            if User.objects.filter(username=id_number).exists():
                messages.error(request, 'رقم الهوية هذا مسجل مسبقاً في النظام كوصي.')
            else:
                user = User.objects.create_user(username=id_number, email=email, password=password)
                
                Guardian.objects.create(
                    user=user,
                    name=name,
                    id_number=id_number,
                    phone=phone,
                    payout_method=payout_method,
                    payout_details=payout_details,
                    id_document=id_document,
                    is_approved=True 
                )
                messages.success(request, 'تم إنشاء حساب الوصي بنجاح.')

        elif action == 'edit':
            guardian_id = request.POST.get('guardian_id')
            guardian = get_object_or_404(Guardian, id=guardian_id)
            
            guardian.name = request.POST.get('name', guardian.name)
            guardian.id_number = request.POST.get('id_number', guardian.id_number)
            guardian.phone = request.POST.get('phone', guardian.phone)
            guardian.payout_method = request.POST.get('payout_method', guardian.payout_method)
            guardian.payout_details = request.POST.get('payout_details', guardian.payout_details)
            
            new_email = request.POST.get('email')
            if new_email and guardian.user:
                guardian.user.email = new_email
                guardian.user.save()

            if 'id_document' in request.FILES:
                guardian.id_document = request.FILES['id_document']
            
            guardian.save()
            messages.success(request, 'تم تعديل بيانات الوصي بنجاح.')

        return redirect('manage_guardians')

    return render(request, 'Admin-dashboard/manage_guardians.html', {'guardians': guardians})

@login_required(login_url='index')
def delete_guardian(request, guardian_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_guardians')
    
    guardian = get_object_or_404(Guardian, id=guardian_id)
    user = guardian.user
    
    guardian.delete()
    if user:
        user.delete() 
        
    messages.success(request, 'تم حذف الوصي وحساب الدخول الخاص به نهائياً.')
    return redirect('manage_guardians')


@login_required(login_url='login_view')
@user_passes_test(lambda u: u.is_superuser, login_url='index')
def toggle_document_visibility(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(OrphanDocument, id=doc_id)
        
        doc.is_public = not doc.is_public 
        doc.save()
        
        status_text = "مرئياً للكافل" if doc.is_public else "مخفياً عن الكافل"
        messages.success(request, f"تم تحديث المستند '{doc.title}' ليصبح {status_text}.")
        
        return redirect('admin_orphan_details', orphan_id=doc.orphan.id)
        
    return redirect('manage_orphans')