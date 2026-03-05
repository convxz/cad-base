# website/models.py

import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'мужской'),
        ('F', 'женский'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    city = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, default='русский')
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True) # Новое поле
    def __str__(self):
        return f'Профиль для {self.user.username}'
    
    def get_last_security_event(self):
        if self.password_changed_at:
            return f"Пароль изменен: {self.password_changed_at.strftime('%d.%m.%Y')}"
        return f"Аккаунт создан: {self.user.date_joined.strftime('%d.%m.%Y')}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


# class ModelSubmission(models.Model):
#     # Константы статусов
#     STATUS_PENDING  = 'pending'
#     STATUS_APPROVED = 'approved'
#     STATUS_REJECTED = 'rejected'

#     STATUS_CHOICES = [
#         (STATUS_PENDING,  '⏳ На рассмотрении'),
#         (STATUS_APPROVED, '✅ Принята'),
#         (STATUS_REJECTED, '❌ Отклонена'),
#     ]

#     # Основная информация
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, 
#         related_name='submissions', verbose_name='Пользователь'
#     )
#     title = models.CharField(max_length=200, verbose_name='Название модели')
#     category = models.CharField(max_length=255, blank=True, null=True, verbose_name='Тип изделия')
#     standard = models.CharField(max_length=255, blank=True, null=True, verbose_name='Стандарт')
#     description = models.TextField(blank=True, verbose_name='Описание')

#     # ТРИ ПОЛЯ ДЛЯ ФАЙЛОВ (вместо одного model_file)
#     file_stp = models.FileField(upload_to='submissions/models/stp/', blank=True, null=True, verbose_name='Файл STP/STEP')
#     file_igs = models.FileField(upload_to='submissions/models/igs/', blank=True, null=True, verbose_name='Файл IGS/IGES')
#     file_stl = models.FileField(upload_to='submissions/models/stl/', blank=True, null=True, verbose_name='Файл STL')

#     thumbnail = models.ImageField(upload_to='submissions/thumbnails/', null=True, blank=True, verbose_name='Превью')
    
#     # Администрирование
#     status = models.CharField(
#         max_length=20, choices=STATUS_CHOICES, 
#         default=STATUS_PENDING, db_index=True, verbose_name='Статус'
#     )
#     admin_comment = models.TextField(blank=True, verbose_name='Комментарий администратора')
    
#     created_at = models.DateTimeField(default=timezone.now, verbose_name='Создана')
#     reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Рассмотрена')
#     reviewed_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, blank=True,
#         related_name='reviewed_submissions', verbose_name='Проверил'
#     )

#     class Meta:
#         verbose_name = 'Заявка на модель'
#         verbose_name_plural = 'Заявки на модели'
#         ordering = ['-created_at']

#     def __str__(self):
#         return f'{self.title} ({self.get_status_display()})'

#     # Свойства для проверки статуса
#     @property
#     def is_pending(self):
#         return self.status == self.STATUS_PENDING

#     @property
#     def is_approved(self):
#         return self.status == self.STATUS_APPROVED

#     @property
#     def is_rejected(self):
#         return self.status == self.STATUS_REJECTED

#     # Метод для получения списка загруженных форматов
#     def get_available_formats(self):
#         formats = []
#         if self.file_stp: formats.append('STP')
#         if self.file_igs: formats.append('IGS')
#         if self.file_stl: formats.append('STL')
#         return ", ".join(formats) if formats else "Нет файлов"
    
#     @property
#     def model_extension(self):
#         """Отображает доступные форматы в карточке."""
#         exts = []
#         if self.file_stp: exts.append('STP')
#         if self.file_igs: exts.append('IGS')
#         if self.file_stl: exts.append('STL')
#         return " / ".join(exts) if exts else "—"
    
from django.db import models
from django.utils import timezone

class ModelSubmission(models.Model):
    # Основная информация
    title = models.CharField(max_length=200, verbose_name='Название изделия')
    category = models.CharField(max_length=255, blank=True, null=True, verbose_name='Тип изделия')
    standard = models.CharField(max_length=255, blank=True, null=True, verbose_name='Стандарт (ГОСТ/ISO)')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Файлы (оставляем три формата, как в ТЗ)
    file_stp = models.FileField(upload_to='models/stp/', blank=True, null=True, verbose_name='Файл STP')
    file_igs = models.FileField(upload_to='models/igs/', blank=True, null=True, verbose_name='Файл IGS')
    file_stl = models.FileField(upload_to='models/stl/', blank=True, null=True, verbose_name='Файл STL')

    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True, verbose_name='Превью (фото)')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def model_extension(self):
        """Логика для плашки на карточке"""
        exts = []
        if self.file_stp: exts.append('STP')
        if self.file_igs: exts.append('IGS')
        if self.file_stl: exts.append('STL')
        return " / ".join(exts) if exts else "—"


class ChatRoom(models.Model):
    submission = models.OneToOneField(
        ModelSubmission, on_delete=models.CASCADE,
        related_name='chat_room', verbose_name='Заявка'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Чат-комната'
        verbose_name_plural = 'Чат-комнаты'

    def __str__(self):
        return f'Чат: {self.submission.title}'


class ChatMessage(models.Model):
    room      = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages', verbose_name='Отправитель')
    body      = models.TextField(blank=True, verbose_name='Текст')
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_read   = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering            = ['created_at']

    @property
    def sender_is_admin(self):
        """Используется в views и шаблонах."""
        return self.sender.is_staff or self.sender.is_superuser

    def __str__(self):
        return f'{self.sender.username}: {self.body[:40]}'


class NewsItem(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок новости")
    image = models.ImageField(upload_to='news_previews/', verbose_name="Превью (картинка)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    
    # Поле для полной статьи (если планируете открывать новость по клику)
    content = models.TextField(verbose_name="Текст новости", blank=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name = "Новости"
        ordering = ['-created_at'] # Свежие новости всегда сверху

    def __str__(self):
        return self.title
    

class Document(models.Model):
    standard_number = models.CharField(max_length=100, verbose_name="Номер / Стандарт")
    name = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(upload_to='documents/pdfs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    
    # Поле для счетчика скачиваний (использовали в шаблоне)
    downloads_count = models.PositiveIntegerField(default=0, verbose_name="Кол-во скачиваний")

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документация"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.standard_number} - {self.name}"


    def get_extension(self):
        if not self.file:
            return ""
        # Достаем расширение из пути файла и переводим в верхний регистр (без точки)
        extension = os.path.splitext(self.file.name)[1][1:].upper()
        return extension # Вернет 'PDF', 'DOCX', 'XLSX' и т.д.