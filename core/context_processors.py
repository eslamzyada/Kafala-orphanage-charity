from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        all_notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        return {
            'nav_notifications': all_notifs[:5], 
            'unread_count': all_notifs.filter(is_read=False).count() 
        }
    return {}

