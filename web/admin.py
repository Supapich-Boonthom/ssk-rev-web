from django.contrib import admin
from .models import Place, Review, ReviewLike, ReviewReport


@admin.action(description="อนุมัติสถานที่ที่เลือก")
def approve_places(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_approved", "created_by", "created_at")
    list_filter = ("is_approved", "category")
    search_fields = ("name", "address")
    actions = [approve_places]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("place__name", "user__username", "comment")


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ("review", "reason", "user", "created_at")
    list_filter = ("reason", "created_at")
