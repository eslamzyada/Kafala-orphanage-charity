import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from .models import Orphan, Donor, Sponsorship, Payment, Notification, Document
import json
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import random
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import google.generativeai as genai
import requests
import os


genai.configure(api_key="gen-lang-client-0882826838")

@csrf_exempt 
def kafala_ai_assistant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            api_key = os.getenv('GEMINI_API_KEY')
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

            if request.user.is_authenticated and request.user.is_staff:
                system_instruction = """
                أنت مساعد الإدارة الذكي والنخبة في لوحة تحكم منصة "كفالة" لرعاية الأيتام.
                أنت تتحدث الآن مع "مدير النظام" (الآدمن)، وهو الشخص الذي يمتلك الصلاحيات المطلقة والكاملة للتحكم في كل أجزاء المنصة.
                
                يجب أن تعلم أن مدير النظام يمكنه القيام بما يلي من خلال لوحة التحكم الخاصة به:
                1. إدارة الكفلاء (المتبرعين): عرض بياناتهم، تعديل تفاصيل حساباتهم، إيقاف أو حذف حسابات الكفلاء بالكامل.
                2. إدارة الأيتام: إضافة أيتام جدد، تعديل بياناتهم وحالتهم (الصحية والاجتماعية)، وحذف السجلات إذا لزم الأمر.
                3. إدارة الكفالات: ربط الكفلاء بالأيتام، متابعة حالة الكفالات (نشطة، منتهية، بانتظار الدفع)، وإلغاؤها.
                4. الإدارة المالية: مراجعة واعتماد الحوالات البنكية وإيصالات الدفع اليدوية، والاطلاع على الإحصائيات المالية.
                5. إدارة الوثائق: رفع التقارير المدرسية والصحية وتحديثها.
                
                قواعد الإجابة:
                - أجب باحترافية شديدة وبصيغة الاحترام والتقدير للمدير.
                - إذا سألك المدير عن كيفية التعديل أو الحذف، أخبره أن الصلاحيات متوفرة، ووجهه للذهاب إلى "القسم المخصص" (مثل قسم إدارة الكفلاء أو إدارة الأيتام) في القائمة الجانبية لإجراء التعديل.
                - لا تقل أبداً "لا تتوفر صلاحية"، لأن المدير يملك كل الصلاحيات.
                """
            else:
                system_instruction = """
                أنت موظف دعم فني محترف في منصة "كفالة" للأيتام. 
                أجب دائماً باللغة العربية الفصحى باختصار، وبشكل مباشر وودود. 
                معلومات المنصة: الدفع متاح عبر البطاقات الائتمانية (Stripe) و PalPay. 
                يمكن للكفيل متابعة تقارير اليتيم من صفحة "إدارة كفالاتي". 
                لا تخترع أي معلومات غير موجودة هنا.
                """

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
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
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            
            if user.is_superuser:
                return redirect('/admin-dashboard/') 
            elif Donor.objects.filter(email=user.email).exists():
                return redirect('sponsor_dashboard')
            elif Orphan.objects.filter(username=user.username).exists():
                return redirect('orphan_dashboard')
            else:
                return redirect('index')
        else:
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
            username = request.POST.get('orphan_username')
            password = request.POST.get('orphan_password')
            name = request.POST.get('orphan_name')
            
            age = request.POST.get('orphan_age')
            gender = request.POST.get('orphan_gender')
            area = request.POST.get('orphan_area')
            social_status = request.POST.get('orphan_social')
            health_status = request.POST.get('orphan_health')
            image = request.FILES.get('orphan_photo')
            
            if username and password and name:
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(username=username, password=password)
                    Orphan.objects.create(
                        username=username,  
                        name=name,          
                        age=age if age else None,
                        gender=gender,
                        area=area,
                        social_status=social_status,
                        health_status=health_status,
                        image=image
                    )
                    login(request, user)
                    return redirect('orphan_dashboard')
                else:
                    print("Error: Username already exists!")
                    return redirect('index')
                    
    return redirect('index')

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
    
    search_query = request.GET.get('q')
    if search_query:
        orphans = Orphan.objects.filter(name__icontains=search_query).order_by('-created_at')
    else:
        orphans = Orphan.objects.all().order_by('-created_at')
        
    return render(request, 'Admin-dashboard/Orphanage.html', {'orphans': orphans})

def add_orphan(request):
    if request.method == 'POST':
        username = request.POST.get('username') 
        name = request.POST.get('name') 
        password = request.POST.get('password') 
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        area = request.POST.get('area')
        health_status = request.POST.get('health_status')
        social_status = request.POST.get('social_status')
        
        if User.objects.filter(username=username).exists():
            return redirect('manage_orphans')

        User.objects.create_user(username=username, password=password)
        
        orphan = Orphan.objects.create(
            username=username, 
            name=name,         
            age=age,
            gender=gender,
            area=area,
            health_status=health_status,
            social_status=social_status,
        )
        
        if 'image' in request.FILES:
            orphan.image = request.FILES['image']
            orphan.save()
            
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
            
        return redirect('manage_orphans')
        
    return render(request, 'Admin-dashboard/newOrphan.html')

@login_required(login_url='index')
def admin_orphan_details(request, orphan_id):
    if not request.user.is_superuser:
        return redirect('index')
    
    orphan = get_object_or_404(Orphan, id=orphan_id)
    documents = orphan.documents.all()
    sponsorships = orphan.sponsorships.all()
    upload_error = None
    
    if request.method == 'POST':
        if 'edit_orphan' in request.POST:
            orphan.name = request.POST.get('name', orphan.name)
            orphan.age = request.POST.get('age', orphan.age)
            orphan.area = request.POST.get('area', orphan.area)
            orphan.social_status = request.POST.get('social_status', orphan.social_status)
            orphan.health_status = request.POST.get('health_status', orphan.health_status)
            orphan.save()
            return redirect('admin_orphan_details', orphan_id=orphan.id)
        
        elif 'upload_document' in request.POST:
            uploaded_file = request.FILES.get('document_file')
            if not uploaded_file:
                upload_error = "No file uploaded."
            else:
                try:
                    _save_document_for_orphan(
                        orphan,
                        uploaded_file,
                        request.POST.get('document_title', 'Untitled Document'),
                        request.POST.get('document_desc', ''),
                    )
                except ValidationError as exc:
                    upload_error = " ".join(exc.messages)
            if not upload_error:
                return redirect('admin_orphan_details', orphan_id=orphan.id)
            
    context = {
        'orphan': orphan,
        'documents': documents,
        'sponsorships': sponsorships,
        'upload_error': upload_error,
    }
    return render(request, 'Admin-dashboard/ShowOrphan.html', context)

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
    payments = Payment.objects.select_related('sponsorship__donor', 'sponsorship__orphan').all().order_by('-created_at')
    return render(request, 'Admin-dashboard/paymentsManagement.html', {'payments': payments})

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required(login_url='index')
def create_stripe_checkout_session(request, payment_id):
    try:
        donor = Donor.objects.get(email=request.user.email)
        payment = get_object_or_404(Payment, id=payment_id, sponsorship__donor=donor)
        
        amount_in_cents = int(payment.amount * 100)
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'كفالة اليتيم: {payment.sponsorship.orphan.name}',
                        'description': 'دفعة كفالة دورية',
                    },
                    'unit_amount': amount_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            client_reference_id=payment.id, 
            
            success_url=request.build_absolute_uri(reverse('donor_payments')) + '?success=true',
            cancel_url=request.build_absolute_uri(reverse('pay_checkout', args=[payment.id])) + '?canceled=true',
        )
        return redirect(checkout_session.url)
        
    except Exception as e:
        return redirect('donor_payments')

@login_required(login_url='index')
def notifications_view(request):
    if not request.user.is_superuser:
        return redirect('index')
    notifications = Notification.objects.all().order_by('-created_at')
    recent_notifications = Notification.objects.all().order_by('-created_at')[:5]
    
    return render(request, 'Admin-dashboard/notifications.html', {
        'notifications': notifications,
        'recent_notifications': recent_notifications
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

# ================= SPONSORSHIP ACTION VIEWS =================

@login_required(login_url='index')
def accept_sponsorship(request, spon_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
    
    spon = get_object_or_404(Sponsorship, id=spon_id)
    spon.status = 'Active'
    spon.save()
    
    # Update the Orphan's status to Sponsored
    spon.orphan.sponsorship_status = 'Sponsored'
    spon.orphan.save()
    
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def reject_sponsorship(request, spon_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
    
    spon = get_object_or_404(Sponsorship, id=spon_id)
    # Rejecting just deletes the pending request to keep the database clean
    spon.delete() 
    
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def end_sponsorship(request, spon_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
    
    spon = get_object_or_404(Sponsorship, id=spon_id)
    spon.status = 'Ended'
    spon.save()
    
    # Free up the orphan so they can be sponsored again
    if not Sponsorship.objects.filter(orphan=spon.orphan, status='Active').exists():
        spon.orphan.sponsorship_status = 'Available'
        spon.orphan.save()
        
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def renew_sponsorship(request, spon_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
    
    spon = get_object_or_404(Sponsorship, id=spon_id)
    spon.status = 'Active'
    spon.save()
    
    # Ensure Orphan is marked as Sponsored again
    spon.orphan.sponsorship_status = 'Sponsored'
    spon.orphan.save()
    
    return redirect('manage_sponsorships')

@login_required(login_url='index')
def delete_sponsorship(request, spon_id):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('manage_sponsorships')
    
    spon = get_object_or_404(Sponsorship, id=spon_id)
    orphan = spon.orphan
    spon.delete()
    
    # Double check if the orphan needs to be marked as available
    if not Sponsorship.objects.filter(orphan=orphan, status='Active').exists():
        orphan.sponsorship_status = 'Available'
        orphan.save()
        
    return redirect('manage_sponsorships')


# ============= ORPHAN DASHBOARD VIEWS =============

@login_required(login_url='index')
def orphan_dashboard(request):
    try:
        orphan = Orphan.objects.get(username=request.user.username)
        sponsorship = Sponsorship.objects.filter(orphan=orphan, status='Active').first()
        unread_count = Notification.objects.filter(orphan=orphan, is_read=False).count()
        recent_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')[:5]
    except Orphan.DoesNotExist:
        orphan, sponsorship, unread_count, recent_notifications = None, None, 0, []

    context = {
        'orphan': orphan, 'sponsorship': sponsorship, 
        'unread_count': unread_count, 'recent_notifications': recent_notifications
    }
    return render(request, 'Orphan-dashboard/dashboard.html', context)

@login_required(login_url='index')
def orphan_details(request):
    try:
        orphan = Orphan.objects.get(username=request.user.username)
        unread_count = Notification.objects.filter(orphan=orphan, is_read=False).count()
        recent_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')[:5]
    except Orphan.DoesNotExist:
        orphan, unread_count, recent_notifications = None, 0, []
        
    return render(request, 'Orphan-dashboard/detailedOrphan.html', {'orphan': orphan, 'unread_count': unread_count, 'recent_notifications': recent_notifications})

@login_required(login_url='index')
def orphan_documents(request):
    try:
        orphan = Orphan.objects.get(username=request.user.username)
        unread_count = Notification.objects.filter(orphan=orphan, is_read=False).count()
        recent_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')[:5]
    except Orphan.DoesNotExist:
        orphan, unread_count, recent_notifications = None, 0, []
    
    upload_error = None
    if request.method == 'POST':
        if not orphan:
            return redirect('index')
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            upload_error = "No file uploaded."
        else:
            try:
                _save_document_for_orphan(
                    orphan,
                    uploaded_file,
                    request.POST.get('title'),
                    request.POST.get('description'),
                )
                return redirect('orphan_documents')
            except ValidationError as exc:
                upload_error = " ".join(exc.messages)
                
    # FIXED: Added the documents query so your HTML table actually has data!
    documents = orphan.documents.all() if orphan else []
        
    return render(request, 'Orphan-dashboard/documents.html', {
        'orphan': orphan,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'upload_error': upload_error,
        'documents': documents,
    })

@login_required(login_url='index')
def orphan_sponsorships(request):
    try:
        orphan = Orphan.objects.get(username=request.user.username)
        unread_count = Notification.objects.filter(orphan=orphan, is_read=False).count()
        recent_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')[:5]
    except Orphan.DoesNotExist:
        orphan, unread_count, recent_notifications = None, 0, []
        
    return render(request, 'Orphan-dashboard/Myguarantee.html', {'orphan': orphan, 'unread_count': unread_count, 'recent_notifications': recent_notifications})

@login_required(login_url='index')
def orphan_notifications(request):
    try:
        orphan = Orphan.objects.get(username=request.user.username)
        unread_count = Notification.objects.filter(orphan=orphan, is_read=False).count()
        recent_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')[:5]
        all_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')
    except Orphan.DoesNotExist:
        orphan, unread_count, recent_notifications, all_notifications = None, 0, [], []
        
    return render(request, 'Orphan-dashboard/notifications.html', {
        'orphan': orphan, 
        'unread_count': unread_count, 
        'recent_notifications': recent_notifications,
        'notifications': all_notifications 
    })

@login_required(login_url='index')
def orphan_edit_profile(request):
    try:
        orphan = Orphan.objects.get(username=request.user.username)
        unread_count = Notification.objects.filter(orphan=orphan, is_read=False).count()
        recent_notifications = Notification.objects.filter(orphan=orphan).order_by('-created_at')[:5]
    except Orphan.DoesNotExist:
        orphan, unread_count, recent_notifications = None, 0, []
        return redirect('index') 
        
    if request.method == 'POST':
        new_email = request.POST.get('email')
        if new_email:
            request.user.email = new_email
            request.user.save()

        new_contact_email = request.POST.get('contact_email')
        if new_contact_email:
            orphan.contact_email = new_contact_email
        
        age_val = request.POST.get('age')
        if age_val and age_val.isdigit():
            orphan.age = int(age_val)
            
        orphan.gender = request.POST.get('gender', orphan.gender)
        orphan.area = request.POST.get('area', orphan.area)
        orphan.social_status = request.POST.get('social_status', orphan.social_status)
        orphan.health_status = request.POST.get('health_status', orphan.health_status)
        orphan.health_details = request.POST.get('health_details', orphan.health_details)
        orphan.guardian_name = request.POST.get('guardian_name', orphan.guardian_name)
        orphan.phone = request.POST.get('phone', orphan.phone)

        if 'profile_image' in request.FILES:
            orphan.image = request.FILES['profile_image']

        orphan.save()
        return redirect('orphan_details')

    context = {
        'orphan': orphan, 
        'unread_count': unread_count, 
        'recent_notifications': recent_notifications,
        'is_male': orphan.gender == 'Male' if orphan else False,
        'is_female': orphan.gender == 'Female' if orphan else False,
        'health_excellent': orphan.health_status == 'ممتازة' if orphan else False,
        'health_good': orphan.health_status == 'جيدة' if orphan else False,
        'health_sick': orphan.health_status == 'مريض' if orphan else False,
        'health_special': orphan.health_status == 'ذوي احتياجات خاصة' if orphan else False,
    }
    return render(request, 'Orphan-dashboard/editProfile.html', context)

@login_required(login_url='index')
def mark_notification_read(request, notif_id):
    if request.method == 'POST':
        try:
            orphan = Orphan.objects.get(username=request.user.username)
            notif = Notification.objects.get(id=notif_id, orphan=orphan)
            notif.is_read = True
            notif.save()
            return JsonResponse({'status': 'success'})
        except (Orphan.DoesNotExist, Notification.DoesNotExist):
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)

@login_required(login_url='index')
def mark_all_notifications_read(request):
    if request.method == 'POST':
        try:
            orphan = Orphan.objects.get(username=request.user.username)
            Notification.objects.filter(orphan=orphan, is_read=False).update(is_read=True)
            return JsonResponse({'status': 'success'})
        except Orphan.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)


# =================================================================
#                     SPONSOR / DONOR DASHBOARD VIEWS
# =================================================================

@login_required(login_url='index')
def sponsor_dashboard(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        donor_notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
        unread_count = donor_notifications.filter(is_read=False).count()
        recent_notifications = donor_notifications[:5]
        
        sponsored_count = Sponsorship.objects.filter(donor=donor, status='Active').count()
        available_count = Orphan.objects.exclude(sponsorships__donor=donor).distinct().count()
    except Donor.DoesNotExist:
        # Fallback for Admin testing the dashboard
        donor = None
        unread_count = 0
        recent_notifications = []
        sponsored_count = 0
        available_count = Orphan.objects.filter(sponsorship_status='Available').count()
        
    context = {
        'donor': donor,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
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
        donor_notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
        unread_count = donor_notifications.filter(is_read=False).count()
        recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        donor = None
        sponsorships = []
        unread_count = 0
        recent_notifications = []
        
    context = {
        'donor': donor,
        'sponsorships': sponsorships,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/guarantee.html', context)

from django.utils import timezone

@login_required(login_url='index')
def create_new_sponsorship(request, orphan_id):
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(email=request.user.email)
            orphan = get_object_or_404(Orphan, id=orphan_id)
            
            sponsorship = Sponsorship.objects.create(
                donor=donor,
                orphan=orphan,
                amount=50.00, 
                start_date=timezone.now().date(),
                status='Pending',
                sponsorship_type='Monthly'
            )
            
            first_payment = Payment.objects.create(
                sponsorship=sponsorship,
                amount=sponsorship.amount,
                payment_date=timezone.now().date(),
                status='Pending',
                payment_method='Cash'
            )
            
            return redirect('pay_checkout', payment_id=first_payment.id)
            
        except Donor.DoesNotExist:
            return redirect('sponsor_dashboard')
            
    return redirect('donor_orphans')

@login_required(login_url='index')
def donor_orphans(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        available_orphans = Orphan.objects.exclude(sponsorships__donor=donor).distinct()
        donor_notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
        unread_count = donor_notifications.filter(is_read=False).count()
        recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        donor = None
        available_orphans = Orphan.objects.filter(sponsorship_status='Available')
        unread_count = 0
        recent_notifications = []
        
    # === THE SEARCH BAR ENGINE ===
    query = request.GET.get('q')
    if query:
        available_orphans = available_orphans.filter(name__icontains=query)
        
    context = {
        'donor': donor,
        'orphans': available_orphans,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'user': request.user,
        'search_query': query
    }
    return render(request, 'Donor-dashboard/showOrphan.html', context)


@login_required(login_url='index')
def donor_notifications(request):
    try:
        donor = Donor.objects.get(email=request.user.email)
        notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
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
        donor_notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
        unread_count = donor_notifications.filter(is_read=False).count()
        recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        # Prevent Admins from crashing the edit profile page
        return redirect('sponsor_dashboard')
        
    if request.method == 'POST':
        # CRITICAL FIX: Update BOTH User and Donor emails to prevent lockout!
        new_email = request.POST.get('email')
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            request.user.username = new_email # Assuming username matches email
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
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
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
        payments = Payment.objects.filter(sponsorship__donor=donor).order_by('-payment_date')
        
        donor_notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
        unread_count = donor_notifications.filter(is_read=False).count()
        recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        donor = None
        payments = []
        unread_count = 0
        recent_notifications = []
        
    context = {
        'donor': donor,
        'payments': payments,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'user': request.user
    }
    return render(request, 'Donor-dashboard/payments.html', context)

@login_required(login_url='index')
def pay_checkout(request, payment_id):
    try:
        donor = Donor.objects.get(email=request.user.email)
        payment = get_object_or_404(Payment, id=payment_id, sponsorship__donor=donor, status='Pending')
        
        donor_notifications = Notification.objects.filter(donor=donor).order_by('-created_at')
        unread_count = donor_notifications.filter(is_read=False).count()
        recent_notifications = donor_notifications[:5]
    except Donor.DoesNotExist:
        return redirect('sponsor_dashboard')

    if request.method == 'POST':
        method = request.POST.get('payment_method')
        reference = request.POST.get('transaction_reference', '')
        
        payment.payment_method = method
        
        if method == 'Credit Card':
            payment.save() 
            return redirect('create_stripe_checkout_session', payment_id=payment.id)
            
        elif method in ['Bank', 'PalPay']:
            if 'receipt_image' in request.FILES:
                payment.receipt_image = request.FILES['receipt_image']
            payment.transaction_reference = reference
            payment.save()
            
        elif method == 'Cash':
            payment.transaction_reference = f"CASH-{payment.id}-{random.randint(1000, 9999)}"
            payment.save()
            
        return redirect('donor_payments')

    context = {
        'donor': donor,
        'payment': payment,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
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
