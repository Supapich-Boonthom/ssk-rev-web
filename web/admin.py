from django.contrib import admin
from .models import (
    Place,
    Review,
    ReviewImage,
    ReviewLike,
    ReviewReport,
    Profile,
    Notification,
    Tag,
    Comment,
)


@admin.action(description="อนุมัติสถานที่ที่เลือก")
def approve_places(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "opening_hours",
        "admission_fee",
        "contact",
        "is_approved",
        "created_by",
        "created_at",
    )
    list_filter = ("is_approved", "category")
    search_fields = ("name", "description", "address", "contact")
    actions = [approve_places]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("place__name", "user__username", "comment")
    filter_horizontal = ("tags",)
    inlines = [ReviewImageInline]


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ("review", "image", "created_at")
    list_filter = ("created_at",)


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ("review", "reason", "user", "created_at")
    list_filter = ("reason", "created_at")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "bio")
    search_fields = ("user__username", "bio")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "title", "message")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "review", "content", "created_at")
    search_fields = ("user__username", "content", "review__place__name")
