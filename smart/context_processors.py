from .models import OrderNotification






def global_context(request):
    unviewed_count = OrderNotification.objects.filter(is_viewed=False).count()

    return {
        'count': unviewed_count
    }