import os
import django
import requests
from django.core.files.base import ContentFile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings")
django.setup()

from web.models import Place

places_data = [
    {
        "name": "สวนสมเด็จพระศรีนครินทร์ ศรีสะเกษ",
        "category": "nature",
        "address": "ตำบลหนองครก อำเภอเมืองศรีสะเกษ",
        "description": "สวนสาธารณะเฉลิมพระเกียรติแห่งแรกของประเทศไทย บรรยากาศร่มรื่นเต็มไปด้วยต้นลำดวนกว่า 50,000 ต้น มีสวนสัตว์และพื้นที่พักผ่อนหย่อนใจ",
        "latitude": 15.1017,
        "longitude": 104.3168,
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=15.1017,104.3168",
        "image_url": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?w=1000&auto=format&fit=crop&q=80",
    },
    {
        "name": "วัดมหาพุทธาราม (วัดพระโต)",
        "category": "temple",
        "address": "ตำบลเมืองเหนือ อำเภอเมืองศรีสะเกษ",
        "description": "วัดอารามหลวงคู่บ้านคู่เมือง ประดิษฐานหลวงพ่อโต พระพุทธรูปศักดิ์สิทธิ์ปางมารวิชัยที่เป็นศูนย์รวมจิตใจของชาวศรีสะเกษ",
        "latitude": 15.1189,
        "longitude": 104.3274,
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=15.1189,104.3274",
        "image_url": "https://images.unsplash.com/photo-1548013146-72479768bada?w=1000&auto=format&fit=crop&q=80",
    },
    {
        "name": "ปราสาทสระกำแพงใหญ่",
        "category": "temple",
        "address": "ตำบลสระกำแพงใหญ่ อำเภออุทุมพรพิสัย",
        "description": "โบราณสถานศิลปะขอมโบราณขนาดใหญ่และสมบูรณ์ที่สุดแห่งหนึ่งในจังหวัดศรีสะเกษ สร้างขึ้นในราวพุทธศตวรรษที่ 16",
        "latitude": 15.0864,
        "longitude": 104.1481,
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=15.0864,104.1481",
        "image_url": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=1000&auto=format&fit=crop&q=80",
    },
    {
        "name": "ผามออีแดง",
        "category": "nature",
        "address": "อุทยานแห่งชาติเขาพระวิหาร อำเภอกันทรลักษ์",
        "description": "จุดชมวิวหน้าผาสูงชันริมชายแดนไทย-กัมพูชา ชมทะเลหมอกและภาพแกะสลักนูนต่ำหินทรายโบราณอายุกว่า 1,500 ปี",
        "latitude": 14.3887,
        "longitude": 104.6931,
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=14.3887,104.6931",
        "image_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1000&auto=format&fit=crop&q=80",
    },
    {
        "name": "ถนนคนเดินศรีสะเกษ",
        "category": "market",
        "address": "ถนนเลียบทางรถไฟ อำเภอเมืองศรีสะเกษ",
        "description": "แหล่งรวมอาหารพื้นเมือง สตรีทฟู้ดอีสาน และสินค้าทำมือ เปิดทุกช่วงเย็นวันหยุดสุดสัปดาห์",
        "latitude": 15.1172,
        "longitude": 104.3298,
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=15.1172,104.3298",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1000&auto=format&fit=crop&q=80",
    },
    {
        "name": "หอคอยศรีลำดวนสวรรค์ (Sisaket Aquarium)",
        "category": "nature",
        "address": "เกาะห้วยน้ำคำ อำเภอเมืองศรีสะเกษ",
        "description": "ศูนย์แสดงพันธุ์สัตว์น้ำและหอคอยชมวิวเมืองศรีสะเกษแบบ 360 องศา พร้อมสวนสาธารณะริมบึงน้ำขนาดใหญ่",
        "latitude": 15.1052,
        "longitude": 104.3392,
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=15.1052,104.3392",
        "image_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1000&auto=format&fit=crop&q=80",
    },
]

print("กำลังนำเข้าข้อมูลสถานที่และดาวน์โหลดรูปภาพ...")

for item in places_data:
    img_url = item.pop("image_url", None)
    place, created = Place.objects.update_or_create(name=item["name"], defaults=item)

    # ดาวน์โหลดรูปภาพและบันทึกลง Cloudinary หากยังไม่มีรูป
    if img_url and not place.image:
        try:
            res = requests.get(img_url, timeout=10)
            if res.status_code == 200:
                filename = f"{place.id}_cover.jpg"
                place.image.save(filename, ContentFile(res.content), save=True)
                print(f"📸 อัปโหลดรูปสำเร็จ: {place.name}")
        except Exception as e:
            print(f"⚠️ โหลดรูปไม่สำเร็จสำหรับ {place.name}: {e}")

    print(f"✅ บันทึกข้อมูล: {place.name}")

print("เสร็จสิ้นการ Seed ข้อมูลทั้งหมดเรียบร้อยแล้ว!")
