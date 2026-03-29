from django.utils import timezone
from datetime import timedelta
from core.models import Notification, Sponsorship


def send_notification(user, title, message, link="#"):
    Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        link=link
    )

def check_sponsorship_notifications():
    today = timezone.now().date()
    
    expiring_soon = Sponsorship.objects.filter(
        end_date=today + timedelta(days=7), 
        status='Active'
    )
    for s in expiring_soon:
        send_notification(
            user=s.donor.user,
            title="تذكير: قرب انتهاء الكفالة",
            message=f"تذكير: كفالتك لليتيم ({s.orphan.name}) ستنتهي خلال أسبوع. نأمل منكم التجديد.",
            link="/donor/my-sponsorships/"
        )

    monthly_sponsorships = Sponsorship.objects.filter(sponsorship_type='Monthly', status='Active')
    for s in monthly_sponsorships:
        if s.start_date.day == today.day:
            send_notification(
                user=s.donor.user,
                title="موعد الدفع الشهري",
                message=f"عزيزي الكافل، اليوم هو موعد الدفع الشهري لكفالة ({s.orphan.name}). جزاكم الله خيراً.",
                link="/donor/payments/"
            )


def run_sponsorship_checkups(user):
    """دالة تفحص كفالات المستخدم وترسل تنبيهات الدفع والانتهاء"""
    today = timezone.now().date()
    active_sponsorships = Sponsorship.objects.filter(donor__user=user, status='Active')
    
    for sp in active_sponsorships:
        if sp.end_date == (today + timedelta(days=7)):
            send_notification(
                user=user,
                title="تذكير: انتهاء الكفالة قريبًا",
                message=f"نود إعلامك بأن كفالتك لليتيم ({sp.orphan.name}) ستنتهي خلال أسبوع واحد.",
                link="/donor/my-sponsorships/"
            )

        if sp.sponsorship_type == 'Monthly':
            if today.day == sp.start_date.day:
                send_notification(
                    user=user,
                    title="موعد المساهمة الشهرية",
                    message=f"عزيزي الكافل، اليوم هو موعد دفع المساهمة الشهرية لليتيم ({sp.orphan.name}).",
                    link="/donor/payments/"
                )
        if sp.end_date and sp.end_date <= today:
            sp.status = 'Ended'
            sp.save()
            
            sp.orphan.sponsorship_status = 'Available'
            sp.orphan.save()
            
            send_notification(
                user=user,
                title="انتهت فترة الكفالة",
                message=f"لقد انتهت اليوم فترة كفالتك لليتيم ({sp.orphan.name}). نشكرك على عطائك النبيل.",
                link="/donor/dashboard/"
            )