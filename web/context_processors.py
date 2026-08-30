def unread_notifications(request):
    if request.user.is_authenticated:
        # ดึงแจ้งเตือนที่ผู้ใช้ยังไม่ได้อ่าน
        unread_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.all()[:5]
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
