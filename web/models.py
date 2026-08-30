from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

CATEGORY_CHOICES = [
    ("cafe", "คาเฟ่ / ร้านอาหาร"),
    ("nature", "ธรรมชาติ / สวนสาธารณะ"),
    ("temple", "วัด / วัฒนธรรม"),
    ("market", "ตลาด / ถนนคนเดิน"),
    ("other", "อื่นๆ"),
]


class Place(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสถานที่")
    description = models.TextField(verbose_name="รายละเอียดสถานที่")
    latitude = models.FloatField(blank=True, null=True, verbose_name="ละติจูด")
    longitude = models.FloatField(blank=True, null=True, verbose_name="ลองจิจูด")
    google_maps_url = models.URLField(
        max_length=500, blank=True, null=True, verbose_name="ลิงก์ Google Maps"
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other", verbose_name="หมวดหมู่"
    )
    address = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ที่อยู่ / อำเภอ"
    )
    image = models.ImageField(
        upload_to="places/", blank=True, null=True, verbose_name="รูปภาพหน้าปก"
    )
    is_approved = models.BooleanField(default=False, verbose_name="อนุมัติให้แสดงผล")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ผู้เพิ่มสถานที่"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="แท็กไฮไลต์ (คั่นด้วยจุลภาค)",
        help_text="เช่น มีที่จอดรถ, ถ่ายรูปสวย, เปิดดึก, ห้องแอร์",
    )

    class Meta:
        verbose_name = "สถานที่"
        verbose_name_plural = "สถานที่ทั้งหมด"

    def __str__(self):
        return self.name

    def get_tag_list(self):
        """แยกแท็กออกมาเป็น List เพื่อนำไปวนลูปแสดงผลใน Template"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0.0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)


class Bookmark(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookmarks", verbose_name="ผู้บันทึก"
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="bookmarked_by",
        verbose_name="สถานที่โปรด",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "สถานที่โปรด"
        verbose_name_plural = "สถานที่โปรดทั้งหมด"
        unique_together = ("user", "place")

    def __str__(self):
        return f"{self.user.username} saved {self.place.name}"


class Review(models.Model):
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE, related_name="reviews", verbose_name="สถานที่"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้เขียนรีวิว")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="คะแนน (1-5)",
    )
    comment = models.TextField(verbose_name="ความคิดเห็น")
    image = models.ImageField(
        upload_to="reviews/", blank=True, null=True, verbose_name="รูปภาพประกอบ"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "รีวิว"
        verbose_name_plural = "รีวิวทั้งหมด"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.place.name} ({self.rating} ดาว)"


class ReviewLike(models.Model):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="likes", verbose_name="รีวิว"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้กดถูกใจ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "การกดถูกใจรีวิว"
        verbose_name_plural = "การกดถูกใจรีวิวทั้งหมด"
        unique_together = ("review", "user")

    def __str__(self):
        return f"{self.user.username} liked review #{self.review.id}"


class ReviewReport(models.Model):
    REPORT_REASONS = [
        ("profanity", "มีคำหยาบคายหรือไม่สุภาพ"),
        ("fake", "ข้อมูลเท็จ / สแปม / โฆษณา"),
        ("inappropriate_img", "รูปภาพไม่เหมาะสมหรือลามก"),
        ("other", "อื่นๆ"),
    ]

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="รีวิวที่ถูกรายงาน",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้รายงาน")
    reason = models.CharField(
        max_length=30,
        choices=REPORT_REASONS,
        default="profanity",
        verbose_name="เหตุผลการรายงาน",
    )
    details = models.TextField(blank=True, null=True, verbose_name="รายละเอียดเพิ่มเติม")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "การรายงานรีวิว"
        verbose_name_plural = "การรายงานรีวิวทั้งหมด"
        unique_together = ("review", "user")

    def __str__(self):
        return f"Report on Review #{self.review.id} by {self.user.username}"
