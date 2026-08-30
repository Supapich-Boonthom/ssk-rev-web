from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

def optimize_image(image_field, max_size=(1200, 1200), quality=85):
    """ปรับขนาดรูปภาพ หมุนภาพตาม EXIF และบีบอัดเป็น JPEG คุณภาพสูง"""
    if not image_field:
        return image_field

    try:
        img = Image.open(image_field)
        
        # หมุนภาพให้ถูกต้องตามทิศทางที่ถ่ายจากมือถือ (EXIF)
        img = ImageOps.exif_transpose(img)

        # แปลงโหมดสีเป็น RGB ป้องกัน Error ตอนเซฟเป็น JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # ย่อขนาดภาพให้ไม่เกินความกว้าง/สูงที่กำหนด
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)

        # คืนค่าไฟล์รูปภาพที่บีบอัดแล้ว
        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image_field.name.split('.')[0]}.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return image_field
