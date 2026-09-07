import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile

def optimize_image(image_field, max_size=(1200, 1200), quality=85):
    """ปรับขนาดรูปภาพ หมุนภาพตาม EXIF และบีบอัดเป็น JPEG คุณภาพสูง"""
    if not image_field:
        return image_field

    # ข้ามหากเป็นไฟล์ที่บันทึกลง Storage แล้ว (ป้องกันการบีบอัดซ้ำซ้อนตอนเรียก .save())
    if hasattr(image_field, '_committed') and image_field._committed:
        return image_field

    try:
        # รีเซ็ตตำแหน่งอ่านไฟล์ให้เริ่มที่ 0
        if hasattr(image_field, 'seek'):
            image_field.seek(0)

        img = Image.open(image_field)
        
        # หมุนภาพให้ถูกต้องตามทิศทางที่ถ่ายจากมือถือ (EXIF)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # แปลงโหมดสีเป็น RGB ป้องกัน Error ตอนเซฟเป็น JPEG (รองรับ RGBA, P, LA, CMYK ฯลฯ)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # ย่อขนาดภาพให้ไม่เกินความกว้าง/สูงที่กำหนด
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        file_size = output.getbuffer().nbytes
        output.seek(0)

        # ตั้งชื่อไฟล์ใหม่ให้เป็น .jpg โดยรักษาชื่อไฟล์เดิมไว้
        raw_name = getattr(image_field, 'name', 'image.jpg') or 'image.jpg'
        base_name, _ = os.path.splitext(os.path.basename(raw_name))
        if not base_name:
            base_name = 'image'
        clean_name = f"{base_name}.jpg"

        # คืนค่าไฟล์รูปภาพที่บีบอัดแล้ว พร้อมขนาดไฟล์จริง
        return InMemoryUploadedFile(
            file=output,
            field_name='ImageField',
            name=clean_name,
            content_type='image/jpeg',
            size=file_size,
            charset=None
        )
    except Exception as e:
        print(f"Error optimizing image: {e}")
        # หากบีบอัดล้มเหลว รีเซ็ตตำแหน่งอ่านแล้วคืนไฟล์เดิมเพื่อไม่ให้ระบบพัง
        if hasattr(image_field, 'seek'):
            try:
                image_field.seek(0)
            except Exception:
                pass
        return image_field

