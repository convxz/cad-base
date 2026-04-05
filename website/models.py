import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    GENDER_CHOICES = [
        ("M", "мужской"),
        ("F", "женский"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="Аватар"
    )
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Пол"
    )
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    language = models.CharField(max_length=50, default="русский", verbose_name="Язык")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")

    password_changed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата смены пароля"
    )

    favorite_models = models.ManyToManyField(
        "ModelSubmission",
        blank=True,
        related_name="liked_by_profiles",
        verbose_name="Избранные изделия",
    )

    def __str__(self):
        return f"Профиль для {self.user.username}"

    def get_last_security_event(self):
        """Возвращает строку с последним важным событием безопасности"""
        if self.password_changed_at:
            return f"Пароль изменен: {self.password_changed_at.strftime('%d.%m.%Y')}"
        return f"Аккаунт создан: {self.user.date_joined.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def get_display_name(self):
        """Возвращает Имя Фамилия, или никнейм если данные не заполнены"""
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.username

    def get_avatar_url(self):
        """Возвращает путь к аватарке или стандартную картинку"""
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return "/static/img/default-avatar.png"

    def __str__(self):
        return f"Профиль: {self.get_display_name()}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()


from django.db import models
from django.utils import timezone


class ModelSubmission(models.Model):
    """Модель для хранения 3D-изделий в каталоге"""

    title = models.CharField(max_length=200, verbose_name="Название изделия")
    category = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Тип изделия"
    )
    standard = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Стандарт (ГОСТ/ISO)"
    )
    description = models.TextField(blank=True, verbose_name="Описание")

    file_stp = models.FileField(
        upload_to="models/stp/", blank=True, null=True, verbose_name="Файл STP"
    )
    file_igs = models.FileField(
        upload_to="models/igs/", blank=True, null=True, verbose_name="Файл IGS"
    )
    file_stl = models.FileField(
        upload_to="models/stl/", blank=True, null=True, verbose_name="Файл STL"
    )
    # amf
    file_amf = models.FileField(
        upload_to="models/amf/", blank=True, null=True, verbose_name="Файл AMF"
    )
    # obj
    file_obj = models.FileField(
        upload_to="models/obj/", blank=True, null=True, verbose_name="Файл OBJ"
    )

    # dwg
    file_dwg = models.FileField(
        upload_to="models/dwg/", blank=True, null=True, verbose_name="Файл DWG"
    )

    thumbnail = models.ImageField(
        upload_to="thumbnails/", null=True, blank=True, verbose_name="Превью (фото)"
    )

    download_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество скачиваний"
    )
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="Дата добавления"
    )

    class Meta:
        verbose_name = "Модель"
        verbose_name_plural = "Модели"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def model_extension(self):
        """Возвращает строку доступных форматов для плашки на карточке"""
        exts = []
        if self.file_stp:
            exts.append("STP")
        if self.file_igs:
            exts.append("IGS")
        if self.file_stl:
            exts.append("STL")
        if self.file_amf:
            exts.append("AMF")
        if self.file_obj:
            exts.append("OBJ")
        if self.file_dwg:
            exts.append("DWG")
        return " / ".join(exts) if exts else "—"


class ChatRoom(models.Model):

    submission = models.OneToOneField(
        "ModelSubmission",
        on_delete=models.CASCADE,
        related_name="chat_room",
        null=True,
        blank=True,
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="support_chat", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_client(self):

        return self.user

    class Meta:
        verbose_name = "Чат-комната"
        verbose_name_plural = "Чат-комнаты"


class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name="Отправитель",
    )
    body = models.TextField(blank=True, verbose_name="Текст")
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_read = models.BooleanField(default=False)
    file = models.FileField(
        upload_to="chat_files/", blank=True, null=True, verbose_name="Файл"
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["created_at"]

    @property
    def sender_is_admin(self):
        """Используется в views и шаблонах."""
        return self.sender.is_staff or self.sender.is_superuser

    def __str__(self):
        return f"{self.sender.username}: {self.body[:40]}"


class NewsItem(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок новости")
    image = models.ImageField(
        upload_to="news_previews/", verbose_name="Превью (картинка)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    content = models.TextField(verbose_name="Текст новости", blank=True)

    views_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество просмотров"
    )

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Document(models.Model):
    standard_number = models.CharField(max_length=100, verbose_name="Номер / Стандарт")
    name = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(upload_to="documents/pdfs/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    is_drawing = models.BooleanField(default=False, verbose_name="Это чертеж?")

    downloads_count = models.PositiveIntegerField(
        default=0, verbose_name="Кол-во скачиваний"
    )

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документация"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.standard_number} - {self.name}"

    def get_extension(self):
        if not self.file:
            return ""

        extension = os.path.splitext(self.file.name)[1][1:].upper()
        return extension


class DownloadLog(models.Model):

    model_item = models.ForeignKey(
        ModelSubmission, on_delete=models.SET_NULL, null=True, verbose_name="Изделие"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )

    file_format = models.CharField(max_length=10, verbose_name="Формат (STP/STL/IGS)")

    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP адрес"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    class Meta:
        verbose_name = "Лог скачивания"
        verbose_name_plural = "Логи скачиваний"
        ordering = ["-timestamp"]

    def __str__(self):
        user_display = self.user.username if self.user else f"Гость ({self.ip_address})"
        return f"{user_display} скачал {self.model_item} ({self.file_format})"
