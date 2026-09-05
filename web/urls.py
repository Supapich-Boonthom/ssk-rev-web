from django.urls import path
from . import views

urlpatterns = [
    path("", views.place_list, name="place_list"),
    path("place/<int:pk>/", views.place_detail, name="place_detail"),
    path("place/add/", views.add_place_view, name="add_place"),  # URL เสนอสถานที่
    path("review/<int:review_id>/like/", views.toggle_like_review, name="toggle_like"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "review/<int:review_id>/report/", views.report_review_view, name="report_review"
    ),
    path(
        "place/<int:place_id>/bookmark/",
        views.toggle_bookmark_view,
        name="toggle_bookmark",
    ),
    path("profile/", views.profile_view, name="profile"),
    path("set-badge/", views.set_featured_badge, name="set_featured_badge"),
    path("user/<str:username>/", views.user_profile_view, name="user_profile"),
    path("review/<int:pk>/delete/", views.delete_review, name="delete_review"),
    path("review/<int:pk>/edit/", views.edit_review, name="edit_review"),
    path("notification/<int:pk>/read/", views.read_notification, name="read_notification"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="mark_all_read"),
    path("review/quick/", views.quick_review, name="quick_review"),
    path("review/<int:review_id>/comment/", views.add_comment, name="add_comment"),
]
