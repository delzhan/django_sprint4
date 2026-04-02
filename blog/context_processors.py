from .models import Notification

def unread_notifications_count(request):
    """Возвращает количество непрочитанных уведомлений."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}

def recent_notifications(request):
    """Возвращает последние 5 уведомлений для текущего пользователя."""
    if request.user.is_authenticated:
        recent = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {'recent_notifications': recent}
    return {'recent_notifications': []}