import re

# รายการคำหยาบหรือคำไม่เหมาะสม (สามารถเพิ่มคำที่ต้องการบล็อกได้เรื่อยๆ)
BANNED_WORDS = [
    "ควย",
    "เหี้ย",
    "สัตว์",
    "เย็ด",
    "มึง",
    "กู",
    "สัส",
    "ดอกทอง",
    "เงี่ยน",
    "หี",
    "แตด",
    "เยด",
    "ระยำ",
    "สันดาน",
    "กวนส้นตีน",
    "fuck",
    "shit",
    "bitch",
    "dick",
    "pussy",
    "asshole",
]


def mask_profanity(text: str) -> str:
    """แปลงคำหยาบให้เป็นดอกจัน เช่น 'ร้านนี้เหี้ยมาก' -> 'ร้านนี้***มาก'"""
    if not text:
        return text

    cleaned_text = text
    for word in BANNED_WORDS:
        # ใช้ regex แทนที่แบบ case-insensitive
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        cleaned_text = pattern.sub("*" * len(word), cleaned_text)

    return cleaned_text
