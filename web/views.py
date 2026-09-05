from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from .models import (
    Place,
    Review,
    ReviewImage,
    ReviewLike,
    CATEGORY_CHOICES,
    ReviewReport,
    Bookmark,
    Notification,
    Tag,
)
from .forms import (
    RegisterForm,
    ReviewForm,
    PlaceForm,
    ProfileUpdateForm,
    QuickReviewForm,
)
from .moderation import mask_profanity


def place_list(request):
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    tab = request.GET.get("tab", "places")
    feed_filter = request.GET.get("sort", "trending")
    selected_filter = request.GET.get("filter", "")
    saved = request.GET.get("saved", "")
    selected_tag = request.GET.get("tag", "")

    places = (
        Place.objects.filter(is_approved=True)
        .annotate(reviews_count=Count("reviews"))
        .prefetch_related("reviews")
    )
    if (selected_filter == "saved" or saved == "true") and request.user.is_authenticated:
        places = places.filter(bookmarked_by__user=request.user)
    elif saved == "true" and not request.user.is_authenticated:
        places = places.none()
    elif category:
        places = places.filter(category=category)

    if query:
        places = places.filter(
            Q(name__icontains=query)
            | Q(address__icontains=query)
            | Q(description__icontains=query)
        )

    # กรองสถานที่ตามแท็กของรีวิว
    if selected_tag:
        places = places.filter(reviews__tags__name=selected_tag).distinct()

    # ดึงแท็กทั้งหมดสำหรับแสดงปุ่มกรอง
    all_tags = Tag.objects.all()

    # ดึงข้อมูลรีวิวเฉพาะเมื่อเปิดแท็บฟีด (feed) เพื่อประหยัด Query และเวลาโหลด
    recent_reviews = []
    if tab == "feed":
        reviews_qs = (
            Review.objects.filter(place__is_approved=True)
            .select_related("place", "user__profile")
            .prefetch_related("images")
        )
        if feed_filter == "latest":
            recent_reviews = reviews_qs.annotate(likes_count=Count("likes")).order_by(
                "-created_at"
            )
        elif feed_filter == "trending":
            one_week_ago = timezone.now() - timedelta(days=7)
            recent_reviews = reviews_qs.annotate(
                weekly_likes=Count("likes", filter=Q(likes__created_at__gte=one_week_ago)),
                likes_count=Count("likes"),
            ).order_by("-weekly_likes", "-created_at")
        else:  # top
            recent_reviews = reviews_qs.annotate(likes_count=Count("likes")).order_by(
                "-likes_count", "-created_at"
            )

    user_liked_review_ids = []
    user_bookmarked_place_ids = []
    if request.user.is_authenticated:
        if tab == "feed":
            user_liked_review_ids = ReviewLike.objects.filter(
                user=request.user
            ).values_list("review_id", flat=True)
        user_bookmarked_place_ids = Bookmark.objects.filter(
            user=request.user
        ).values_list("place_id", flat=True)

    return render(
        request,
        "place_list.html",
        {
            "places": places,
            "categories": CATEGORY_CHOICES,
            "selected_category": category,
            "query": query,
            "recent_reviews": recent_reviews,
            "user_liked_review_ids": list(user_liked_review_ids),
            "user_bookmarked_place_ids": list(user_bookmarked_place_ids),
            "current_tab": tab,
            "feed_filter": feed_filter,
            "selected_filter": selected_filter,
            "all_tags": all_tags,
            "selected_tag": selected_tag,
        },
    )


def place_detail(request, pk):
    place = get_object_or_404(
        Place.objects.prefetch_related("reviews"), pk=pk
    )
    reviews = (
        place.reviews.annotate(likes_count=Count("likes"))
        .select_related("user__profile")
        .prefetch_related("tags", "images")
        .order_by("-likes_count", "-created_at")
    )
    form = ReviewForm()

    user_liked_review_ids = []
    is_bookmarked = False
    if request.user.is_authenticated:
        user_liked_review_ids = ReviewLike.objects.filter(
            user=request.user
        ).values_list("review_id", flat=True)
        is_bookmarked = Bookmark.objects.filter(user=request.user, place=place).exists()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.warning(request, "กรุณาเข้าสู่ระบบก่อนเขียนรีวิว")
            return redirect("login")

        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.place = place
            review.user = request.user
            review.save()

            # ดึงไฟล์ทั้งหมดที่ผู้ใช้เลือกพร้อมกัน
            images = request.FILES.getlist("upload_images")
            for img in images:
                ReviewImage.objects.create(review=review, image=img)

            # เผื่อกรณีเลือกไฟล์เดียวผ่าน name="image" ด้วย
            if "image" in request.FILES and not images:
                ReviewImage.objects.create(review=review, image=request.FILES["image"])

            messages.success(request, "บันทึกรีวิวของคุณเรียบร้อยแล้ว!")
            return redirect("place_detail", pk=pk)

    return render(
        request,
        "place_detail.html",
        {
            "place": place,
            "reviews": reviews,
            "form": form,
            "user_liked_review_ids": list(user_liked_review_ids),
            "is_bookmarked": is_bookmarked,
        },
    )


@login_required(login_url="login")
def add_place_view(request):
    if request.method == "POST":
        form = PlaceForm(request.POST, request.FILES)
        if form.is_valid():
            place = form.save(commit=False)
            place.created_by = request.user
            place.is_approved = False  # รอแอดมินอนุมัติใน Django Admin
            place.save()
            messages.success(
                request,
                "ส่งข้อมูลสถานที่เรียบร้อยแล้ว! ข้อมูลจะแสดงผลหลังจากทีมงานตรวจสอบ",
            )
            return redirect("place_list")
    else:
        form = PlaceForm()
    return render(request, "add_place.html", {"form": form})


@login_required(login_url="login")
def toggle_like_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    like = ReviewLike.objects.filter(review=review, user=request.user).first()

    if like:
        like.delete()
    else:
        ReviewLike.objects.create(review=review, user=request.user)
        # สร้างการแจ้งเตือนสำหรับเจ้าของรีวิว (ยกเว้นกดถูกใจรีวิวตัวเอง)
        if review.user != request.user:
            Notification.objects.create(
                user=review.user,
                title="มีคนถูกใจรีวิวของคุณ ❤️",
                message=f"{request.user.username} ถูกใจรีวิวของคุณที่ '{review.place.name}'",
                link=f"/place/{review.place.pk}/",
            )

    return redirect(request.META.get("HTTP_REFERER", "place_list"))


def register_view(request):
    if request.user.is_authenticated:
        return redirect("place_list")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            messages.success(request, "สมัครสมาชิกและเข้าสู่ระบบสำเร็จ!")
            return redirect("place_list")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("place_list")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"ยินดีต้อนรับกลับ, {user.username}!")
            next_url = request.GET.get("next", "place_list")
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "ออกจากระบบเรียบร้อยแล้ว")
    return redirect("place_list")


@login_required(login_url="login")
def report_review_view(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == "POST":
        reason = request.POST.get("reason", "profanity")
        details = request.POST.get("details", "")

        report, created = ReviewReport.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={"reason": reason, "details": details},
        )
        if created:
            messages.success(request, "ขอบคุณที่แจ้งรายงาน ทีมงานจะรีบตรวจสอบข้อมูลโดยเร็วครับ")
        else:
            messages.info(request, "คุณได้รายงานรีวิวนี้ไปก่อนหน้านี้แล้ว")

    return redirect(request.META.get("HTTP_REFERER", "place_list"))


@login_required(login_url="login")
def toggle_bookmark_view(request, place_id):
    place = get_object_or_404(Place, pk=place_id)
    bookmark = Bookmark.objects.filter(user=request.user, place=place)

    if bookmark.exists():
        bookmark.delete()
        messages.info(request, f"ลบ {place.name} ออกจากรายการโปรดแล้ว")
    else:
        Bookmark.objects.create(user=request.user, place=place)
        messages.success(request, f"บันทึก {place.name} เข้าสิ่งที่อยากไปแล้ว!")

    return redirect(request.META.get("HTTP_REFERER", "place_list"))


@login_required(login_url="login")
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "อัปเดตโปรไฟล์ของคุณเรียบร้อยแล้ว!")
            return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=profile)

    # ดึงรีวิวที่ผู้ใช้คนนี้เคยเขียน
    user_reviews = request.user.review_set.select_related("place").order_by(
        "-created_at"
    )

    # คำนวณเหรียญตรา
    badges = profile.get_badges() if hasattr(profile, "get_badges") else []

    bookmarked_places = Place.objects.filter(bookmarked_by__user=request.user)

    context = {
        "form": form,
        "profile": profile,
        "reviews": user_reviews,
        "badges": badges,
        "total_reviews": user_reviews.count(),
        "bookmarked_places": bookmarked_places,
    }
    return render(request, "profile.html", context)


def user_profile_view(request, username):
    profile_user = get_object_or_404(
        User.objects.select_related("profile"), username=username
    )
    reviews = profile_user.review_set.select_related("place").order_by("-created_at")
    badges = profile_user.profile.get_badges()
    total_likes = profile_user.profile.total_likes_received()

    context = {
        "profile_user": profile_user,
        "profile": profile_user.profile,
        "reviews": reviews,
        "badges": badges,
        "total_likes": total_likes,
    }
    return render(request, "user_profile.html", context)


@login_required(login_url="login")
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)

    # ตรวจสอบสิทธิ์: หากไม่ใช่เจ้าของรีวิว ให้ตัดสิทธิ์ด้วย Error 403 ทันที
    if review.user != request.user:
        raise PermissionDenied

    if request.method == "POST":
        place_pk = review.place.pk
        review.delete()
        messages.success(request, "ลบรีวิวของคุณเรียบร้อยแล้ว")
        referer = request.META.get("HTTP_REFERER")
        if referer:
            return redirect(referer)
        return redirect("place_detail", pk=place_pk)

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("place_detail", pk=review.place.pk)


@login_required(login_url="login")
def edit_review(request, pk):
    review = get_object_or_404(Review, pk=pk)

    # ตรวจสอบสิทธิ์: หากไม่ใช่เจ้าของรีวิว ให้ตัดสิทธิ์ด้วย Error 403 ทันที
    if review.user != request.user:
        raise PermissionDenied

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()

        if rating:
            try:
                review.rating = max(1, min(5, int(rating)))
            except (ValueError, TypeError):
                pass

        if comment:
            review.comment = mask_profanity(comment)

        review.save()

        # แนบรูปเพิ่มเติมหากมีการอัปโหลด
        images = request.FILES.getlist("upload_images")
        for img in images:
            ReviewImage.objects.create(review=review, image=img)

        messages.success(request, "แก้ไขรีวิวของคุณเรียบร้อยแล้ว!")
        return redirect("place_detail", pk=review.place.pk)

    return render(
        request,
        "edit_review.html",
        {
            "review": review,
            "place": review.place,
        },
    )


@login_required(login_url="login")
def read_notification(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect("profile")


@login_required(login_url="login")
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get("HTTP_REFERER", "place_list"))


@login_required(login_url="login")
@require_POST
def set_featured_badge(request):
    badge_name = request.POST.get("badge_name", "").strip()
    profile = request.user.profile

    # ตรวจสอบว่าผู้ใช้มีเหรียญนี้จริงๆ ป้องกันการส่งค่ามั่ว
    unlocked_badges = [b["name"] for b in profile.get_badges()]

    if badge_name in unlocked_badges:
        profile.featured_badge = badge_name
        profile.save()
        messages.success(request, f"ตั้งค่า '{badge_name}' เป็นเหรียญตราหลักเรียบร้อยแล้ว")
    elif badge_name == "":
        profile.featured_badge = None
        profile.save()
        messages.success(request, "ยกเลิกเหรียญตราหลักเรียบร้อยแล้ว")

    return redirect(request.META.get("HTTP_REFERER", "profile"))


@login_required(login_url="login")
def quick_review(request):
    places = Place.objects.filter(is_approved=True).order_by("name")

    if request.method == "POST":
        place_name = request.POST.get("place_name", "").strip()
        rating = request.POST.get("rating", "5")
        comment = request.POST.get("comment", "").strip()

        if not place_name:
            messages.error(request, "กรุณาระบุชื่อสถานที่ที่ต้องการรีวิว")
            return render(
                request,
                "quick_review.html",
                {
                    "approved_places": places,
                    "places": places,
                    "rating": rating,
                    "comment": comment,
                },
            )

        if not comment:
            messages.error(request, "กรุณากรอกความคิดเห็นหรือความประทับใจ")
            return render(
                request,
                "quick_review.html",
                {
                    "approved_places": places,
                    "places": places,
                    "place_name": place_name,
                    "rating": rating,
                },
            )

        # ค้นหาว่ามีชื่อนี้อยู่แล้วไหม ถ้ายังไม่มีให้สร้างขึ้นมาใหม่โดยอัตโนมัติ (is_approved=False)
        place, created = Place.objects.get_or_create(
            name=place_name,
            defaults={
                "is_approved": False,
                "category": "other",
                "description": "สถานที่เพิ่มโดยผู้ใช้ผ่านรีวิวด่วน (รอการตรวจสอบ)",
                "created_by": request.user,
            },
        )

        comment = mask_profanity(comment)
        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                rating_val = 5
        except (ValueError, TypeError):
            rating_val = 5

        # บันทึกรีวิวโดยผูกกับ place ตัวนี้ทันที
        review = Review.objects.create(
            place=place,
            user=request.user,
            rating=rating_val,
            comment=comment,
        )

        # บันทึกรูปภาพหลายรูป (ReviewImage)
        images = request.FILES.getlist("upload_images")
        for img in images:
            ReviewImage.objects.create(review=review, image=img)
        if "image" in request.FILES and not images:
            ReviewImage.objects.create(review=review, image=request.FILES["image"])

        if created:
            messages.success(
                request,
                f"บันทึกรีวิวและเสนอสถานที่ใหม่ '{place.name}' เรียบร้อยแล้ว (รอการตรวจสอบจากผู้ดูแลระบบ)",
            )
        else:
            messages.success(request, f"บันทึกรีวิวสถานที่ '{place.name}' เรียบร้อยแล้ว!")

        return redirect("place_detail", pk=place.pk)

    # GET request
    selected_place_name = ""
    place_id = request.GET.get("place_id")
    if place_id:
        p = Place.objects.filter(pk=place_id).first()
        if p:
            selected_place_name = p.name

    return render(
        request,
        "quick_review.html",
        {
            "approved_places": places,
            "places": places,
            "place_name": selected_place_name,
        },
    )
