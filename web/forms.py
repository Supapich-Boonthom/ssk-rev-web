from django import forms
from django.contrib.auth.models import User
from .models import Place, Review, Profile
from .moderation import mask_profanity


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = [
            "name",
            "category",
            "address",
            "description",
            "google_maps_url",
            "image",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none text-sm",
                    "placeholder": "เช่น คาเฟ่ริมน้ำ, วัดสระกำแพงใหญ่",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none text-sm"
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none text-sm",
                    "placeholder": "เช่น อำเภอเมืองศรีสะเกษ, ถนนอุบล",
                }
            ),
            "google_maps_url": forms.URLInput(
                attrs={
                    "class": "w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none text-sm",
                    "placeholder": "https://maps.app.goo.gl/...",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none text-sm",
                    "placeholder": "บรรยายจุดเด่น เวลาเปิด-ปิด หรือบรรยากาศของสถานที่นี้...",
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "text-xs text-gray-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100"
                }
            ),
        }


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "รหัสผ่าน", "class": "form-input"}
        )
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "ยืนยันรหัสผ่าน", "class": "form-input"}
        )
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "ชื่อผู้ใช้", "class": "form-input"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "อีเมล", "class": "form-input"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "รหัสผ่านไม่ตรงกัน")
        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment", "image"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, f"{i} ดาว") for i in range(5, 0, -1)],
                attrs={
                    "class": "w-full p-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none"
                },
            ),
            "comment": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "แบ่งปันประสบการณ์ ความประทับใจ หรือข้อเสนอแนะ...",
                    "class": "w-full p-3 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none",
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "text-xs text-gray-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100"
                }
            ),
        }

    # เซฟข้อความที่ผ่านการเซ็นเซอร์คำหยาบแล้ว
    def clean_comment(self):
        comment = self.cleaned_data.get("comment", "")
        return mask_profanity(comment)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio']
