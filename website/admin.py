from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

# Создаем "инлайн" для профиля
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительная информация'

# Определяем новый класс для UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Перерегистрируем модель User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile)