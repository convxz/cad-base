import os

from django import forms
from django.contrib.auth.models import User
from .models import Document, ModelSubmission, Profile


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "gender",
            "city",
            "language",
            "birth_date",
            "phone",
            "address",
            "avatar",
        ]
        widgets = {
            "gender": forms.Select(attrs={"class": "custom-select"}),
            "city": forms.TextInput(attrs={"placeholder": "Город"}),
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7 (___) ___ __ __"}),
            "address": forms.TextInput(attrs={"placeholder": "Адрес"}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Имя"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Фамилия"}),
        }


class SignUpForm(forms.ModelForm):
    full_name = forms.CharField(
        label="Имя и Фамилия",
        widget=forms.TextInput(
            attrs={"placeholder": "Введите имя и фамилию", "class": "form-input"}
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"placeholder": "example@mail.com", "class": "form-input"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={"placeholder": "Минимум 8 символов", "class": "form-input"}
        ),
    )

    class Meta:
        model = User
        fields = ["full_name", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        # Разделяем имя и фамилию
        names = self.cleaned_data["full_name"].split()
        if len(names) > 0:
            user.first_name = names[0]
        if len(names) > 1:
            user.last_name = " ".join(names[1:])

        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["standard_number", "name", "is_drawing", "file"]
        widgets = {
            "standard_number": forms.TextInput(
                attrs={"class": "st-input", "placeholder": "ГОСТ 7798-70"}
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "st-input",
                    "placeholder": "Болты с шестигранной головкой",
                }
            ),
            "file": forms.FileInput(attrs={"class": "st-input", "accept": ".pdf"}),
        }


class ModelSubmissionForm(forms.ModelForm):
    class Meta:
        model = ModelSubmission
        fields = [
            "title",
            "category",
            "standard",
            "description",
            "file_stp",
            "file_igs",
            "file_stl",
            "thumbnail",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Название модели",
                    "style": "width: 100%; padding: 12px; border: 1px solid #eee; border-radius: 8px; background: #f8f9fb;",
                }
            ),
            "category": forms.TextInput(
                attrs={
                    "placeholder": "Например: Крепежные изделия",
                    "style": "width: 100%; padding: 12px; border: 1px solid #eee; border-radius: 8px; background: #f8f9fb;",
                }
            ),
            "standard": forms.TextInput(
                attrs={
                    "placeholder": "Например: ГОСТ",
                    "style": "width: 100%; padding: 12px; border: 1px solid #eee; border-radius: 8px; background: #f8f9fb;",
                }
            ),
        }

    def clean_file_stp(self):
        return self.validate_extension("file_stp", [".stp", ".step"])

    def clean_file_igs(self):
        return self.validate_extension("file_igs", [".igs", ".iges"])

    def clean_file_stl(self):
        return self.validate_extension("file_stl", [".stl"])

    def validate_extension(self, field_name, allowed_extensions):
        file = self.cleaned_data.get(field_name)
        if file:
            import os

            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"Ошибка: ожидался формат {allowed_extensions}"
                )
        return file
