from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from cloudinary.models import CloudinaryField
from .utils import optimize_image

CATEGORY_CHOICES = [
    ("cafe", "คาเฟ่ / ร้านอาหาร"),
    ("temple", "วัด / โบราณสถาน"),
    ("nature", "ธรรมชาติ / สวนสาธารณะ"),
    ("learning", "พิพิธภัณฑ์ / แหล่งเรียนรู้"),
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
    opening_hours = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="เวลาทำการ"
    )
    admission_fee = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ค่าเข้าชม"
    )
    contact = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ติดต่อ"
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
    def image_url(self):
        """คืนค่า URL รูปภาพอย่างปลอดภัย หรือ None หากไม่มีรูปภาพ"""
        if self.image:
            try:
                return self.image.url
            except Exception:
                return None
        return None

    @property
    def average_rating(self):
        # ตรวจสอบว่าถูกดึงผ่าน prefetch_related แล้วหรือไม่เพื่อป้องกัน N+1
        if hasattr(self, "_prefetched_objects_cache") and "reviews" in self._prefetched_objects_cache:
            reviews_list = list(self.reviews.all())
            if not reviews_list:
                return 0.0
            return round(sum(r.rating for r in reviews_list) / len(reviews_list), 1)

        reviews = self.reviews.all()
        if not reviews.exists():
            return 0.0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def save(self, *args, **kwargs):
        if self.image:
            self.image = optimize_image(self.image)
        super().save(*args, **kwargs)


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


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "แท็กรีวิว"
        verbose_name_plural = "แท็กรีวิวทั้งหมด"

    def __str__(self):
        return f"#{self.name}"


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
    tags = models.ManyToManyField(Tag, blank=True, related_name="reviews", verbose_name="แท็กรีวิว")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "รีวิว"
        verbose_name_plural = "รีวิวทั้งหมด"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.place.name} ({self.rating} ดาว)"

    def save(self, *args, **kwargs):
        if self.image:
            self.image = optimize_image(self.image)
        super().save(*args, **kwargs)


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review, related_name="images", on_delete=models.CASCADE, verbose_name="รีวิว"
    )
    image = models.ImageField(upload_to="reviews/", verbose_name="รูปภาพประกอบ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "รูปภาพรีวิว"
        verbose_name_plural = "รูปภาพรีวิวทั้งหมด"

    def __str__(self):
        return f"Image for {self.review.place.name} by {self.review.user.username}"

    def save(self, *args, **kwargs):
        if self.image:
            self.image = optimize_image(self.image)
        super().save(*args, **kwargs)


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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = CloudinaryField('image', blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True)
    featured_badge = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="เหรียญตราที่เลือกแสดง"
    )

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return f"https://ui-avatars.com/api/?name={self.user.username}&background=f59e0b&color=fff&bold=true"

    def get_active_badge(self):
        """ดึงเฉพาะเหรียญที่เลือกมาโชว์ หากไม่มีหรือยังไม่เลือก ให้ดึงเหรียญล่าสุด"""
        all_badges = self.get_badges()
        if not all_badges:
            return None
        if self.featured_badge:
            for b in all_badges:
                if b['name'] == self.featured_badge:
                    return b
        return all_badges[-1]

    def get_badges(self):
        """คำนวณเหรียญตราที่ได้รับตามเงื่อนไข"""
        badges = []
        reviews = self.user.review_set.all()
        total_reviews = reviews.count()
        
        # 1. นักรีวิวมือใหม่
        if total_reviews >= 1:
            badges.append({
                'name': 'นักรีวิวมือใหม่',
                'icon': '🌱',
                'desc': 'เขียนรีวิวแรกบน Sisaket Reviews',
                'condition': 'เขียนรีวิวสถานที่บนเว็บไซต์อย่างน้อย 1 ครั้ง',
                'color': 'bg-emerald-50 text-emerald-700 border-emerald-200'
            })
            
        # 2. กูรูคาเฟ่
        cafe_reviews = reviews.filter(place__category='cafe').count()
        if cafe_reviews >= 3:
            badges.append({
                'name': 'กูรูคาเฟ่',
                'icon': '☕',
                'desc': 'รีวิวคาเฟ่และร้านอาหารครบ 3 แห่ง',
                'condition': 'เขียนรีวิวสถานที่หมวดหมู่คาเฟ่และร้านอาหารครบ 3 แห่ง',
                'color': 'bg-amber-50 text-amber-700 border-amber-200'
            })

        # 3. สายบุญ & วัฒนธรรม
        temple_reviews = reviews.filter(place__category='temple').count()
        if temple_reviews >= 2:
            badges.append({
                'name': 'สายวัฒนธรรม',
                'icon': '🏛️',
                'desc': 'รีวิวสถานที่ท่องเที่ยวเชิงวัฒนธรรมครบ 2 แห่ง',
                'condition': 'เขียนรีวิวสถานที่หมวดหมู่วัดและวัฒนธรรมครบ 2 แห่ง',
                'color': 'bg-purple-50 text-purple-700 border-purple-200'
            })

        # 4. เด็กถิ่นศรีสะเกษ
        if total_reviews >= 5:
            badges.append({
                'name': 'เด็กถิ่นศรีสะเกษ',
                'icon': '🏆',
                'desc': 'รีวิวสถานที่รวมครบ 5 แห่ง',
                'condition': 'เขียนรีวิวสถานที่รวมทั้งหมดครบ 5 แห่ง',
                'color': 'bg-orange-50 text-orange-700 border-orange-200'
            })

        # 5. ไทศรีสะเกษตัวจริง
        if total_reviews >= 10:
            badges.append({
                'name': 'ไทศรีสะเกษตัวจริง',
                'icon': '👑',
                'desc': 'รีวิวสถานที่รวมครบ 10 ครั้งขึ้นไป',
                'condition': 'เขียนรีวิวสถานที่รวมทั้งหมดครบ 10 ครั้งขึ้นไป',
                'color': 'bg-yellow-50 text-yellow-800 border-yellow-300'
            })

        # 6. ขวัญใจชาวศรีสะเกษ
        total_likes = self.total_likes_received()
        if total_likes >= 10:
            badges.append({
                'name': 'ขวัญใจชาวศรีสะเกษ',
                'icon': '❤️',
                'desc': 'ได้รับยอดไลก์สะสมจากรีวิวทั้งหมดครบ 10 ไลก์',
                'condition': 'ได้รับยอดกดถูกใจ (Like) สะสมจากรีวิวทั้งหมดครบ 10 ไลก์',
                'color': 'bg-rose-50 text-rose-700 border-rose-200'
            })

        return badges

    def total_likes_received(self):
        """นับยอดไลก์สะสมจากทุกรีวิวที่ผู้ใช้คนนี้เขียน"""
        total = sum(review.likes.count() for review in self.user.review_set.all())
        return total

    def __str__(self):
        return f"{self.user.username} Profile"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class Comment(models.Model):
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="ข้อความ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - {self.content[:20]}"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Notification.objects.create(
            user=instance,
            title="ยินดีต้อนรับสู่ Sisaket Reviews! ✨",
            message="ขอบคุณสำหรับการสมัครสมาชิก เริ่มต้นสำรวจ ค้นหา และแบ่งปันรีวิวสถานที่ท่องเที่ยวหรือร้านอาหารประทับใจในศรีสะเกษกับเราได้เลยครับ",
            link="/"
        )
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
