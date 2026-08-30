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
    path("user/<str:username>/", views.user_profile_view, name="user_profile"),
]
