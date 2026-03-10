# website/views.py

import os
from time import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.views.decorators.http import require_POST
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import F
from django.contrib.auth.models import User


from website.models import ModelSubmission, NewsItem, Profile, Document
from .forms import DocumentForm, UserUpdateForm, ProfileUpdateForm, ModelSubmissionForm
from .forms import SignUpForm

from django.db.models import Q
from django.core.paginator import Paginator

from django.shortcuts import render
from django.db.models import Q
from .models import ChatRoom, DownloadLog, ModelSubmission, ChatMessage

# Декоратор для проверки прав суперпользователя (можно использовать для админки и т.п.)
def superuser_required(user):
    return user.is_superuser

# ══════════════════════════════════════════════════════════════
# Обычные страницы сайта
# ══════════════════════════════════════════════════════════════

def home(request):
    return render(request, 'index.html')

def contacts(request):
    return render(request, 'contacts.html')

def news_list_view(request):
    news = NewsItem.objects.all()
    return render(request, 'news.html', {'news_list': news})

def news_detail_view(request, pk):
    news_item = get_object_or_404(NewsItem, pk=pk)
    NewsItem.objects.filter(pk=pk).update(views_count=F('views_count') + 1)
    return render(request, 'news_detail.html', {'item': news_item})

def documentation(request):
    documents = Document.objects.all().order_by('standard_number')
    return render(request, 'documentation.html', {'documents': documents})

def adocumentation_view(request):
    # Получаем поисковый запрос из GET-параметра 'q'
    query = request.GET.get('q')
    
    if query:
        # Ищем по названию или номеру стандарта (зависит от твоих полей в модели)
        documents = Document.objects.filter(name__icontains=query) | \
                    Document.objects.filter(standard_number__icontains=query)
    else:
        documents = Document.objects.all()
    
    return render(request, 'adocumentation.html', {
        'documents': documents

    })


def document_edit_view(request, pk=None):
    # Если pk есть — редактируем, если нет — создаем новый
    instance = get_object_or_404(Document, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('adocumentation')
    else:
        form = DocumentForm(instance=instance)
    
    return render(request, 'document_form.html', {
        'form': form,
        'edit_mode': pk is not None
    })


    
def about_platform(request):
    return render(request, 'about_platform.html')

def questions(request):
    return render(request, 'questions.html')


# ══════════════════════════════════════════════════════════════
# Каталог одобренных моделей
# ══════════════════════════════════════════════════════════════




def catalog(request):
    # Берем все модели, так как теперь их добавляет только админ
    models_queryset = ModelSubmission.objects.all()

    # 1. Поиск по названию или стандарту
    query = request.GET.get('q')
    if query:
        models_queryset = models_queryset.filter(
            Q(title__icontains=query) | Q(standard__icontains=query)
        )

    # 2. Фильтр по форматам (проверяем, что поле с файлом не пустое)
    selected_formats = request.GET.getlist('formats')
    if selected_formats:
        format_queries = Q()
        if 'STEP' in selected_formats:
            # Проверяем, что поле file_stp не пустое и не None
            format_queries |= Q(file_stp__isnull=False) & ~Q(file_stp='')
        if 'STL' in selected_formats:
            format_queries |= Q(file_stl__isnull=False) & ~Q(file_stl='')
        if 'IGES' in selected_formats:
            format_queries |= Q(file_igs__isnull=False) & ~Q(file_igs='')
        
        models_queryset = models_queryset.filter(format_queries)

    context = {
        'models': models_queryset, # В шаблоне используй {% for item in models %}
        'query': query,
        'selected_formats': selected_formats,
    }
    return render(request, 'catalog.html', context)


def model_detail(request, pk):
    # БЫЛО (с ошибкой):
    # submission = get_object_or_404(ModelSubmission, pk=pk, status=ModelSubmission.STATUS_APPROVED)
    
    # СТАЛО (правильно):
    submission = get_object_or_404(ModelSubmission, pk=pk)
    
    # Логика для "Похожих моделей" (если используешь категорию)
    related = ModelSubmission.objects.filter(category=submission.category).exclude(pk=pk)[:4]

    return render(request, 'model_detail.html', {
        'submission': submission,
        'related': related
    })


# ══════════════════════════════════════════════════════════════
# Авторизация / регистрация
# ══════════════════════════════════════════════════════════════

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Регистрация прошла успешно! Теперь войдите.")
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('settings')
        else:
            # Передаем ошибку напрямую в контекст шаблона
            return render(request, 'login.html', {'error': "Неверный Email или пароль"})
    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    return redirect('/')


@login_required
def settings_view(request):
    is_edit = request.GET.get('edit') == '1'
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('settings') # Возврат в режим просмотра
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # Если не режим редактирования — отключаем поля
    if not is_edit:
        for field in u_form.fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        for field in p_form.fields.values():
            field.widget.attrs['disabled'] = 'disabled'

    return render(request, 'settings.html', {
        'u_form': u_form, 
        'p_form': p_form, 
        'is_edit': is_edit
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def anews_view(request):
    query = request.GET.get('q')
    if query:
        # Фильтруем по заголовку (title) или тексту (content)
        news_items = NewsItem.objects.filter(title__icontains=query)
    else:
        news_items = NewsItem.objects.all()
        
    return render(request, 'anews.html', {'news_items': news_items})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_news_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if title and image: # Простая проверка на обязательные поля
            NewsItem.objects.create(
                title=title,
                content=content,
                image=image
            )
            return redirect('anews') # Возвращаемся в таблицу новостей

    return render(request, 'create_news.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_news_view(request, pk):
    news = get_object_or_404(NewsItem, pk=pk)
    if request.method == 'POST':
        news.title = request.POST.get('title')
        news.content = request.POST.get('content')
        if request.FILES.get('image'):
            news.image = request.FILES.get('image')
        news.save()
        return redirect('anews')
    
    return render(request, 'create_news.html', {'news': news, 'is_edit': True})

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_news_view(request, pk):
    news = get_object_or_404(NewsItem, pk=pk)
    news.delete()
    return redirect('anews')




@login_required
@user_passes_test(lambda u: u.is_superuser)
def model_edit_view(request, pk=None):
    instance = get_object_or_404(ModelSubmission, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = ModelSubmissionForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            model_obj = form.save(commit=False)
            if not pk:
                model_obj.user = request.user
            model_obj.save()
            return redirect('acatalog')
    else:
        form = ModelSubmissionForm(instance=instance)

    # ВОТ ЗДЕСЬ БЫЛА ОШИБКА. Меняем 'model_form.html' на 'amanage_model.html'
    return render(request, 'amanage_model.html', {
        'form': form,
        'edit_mode': pk is not None,
        'instance': instance
    })


def acatalog_view(request):
    # Просто получаем все модели, так как статусов больше нет
    query = request.GET.get('q', '')
    if query:
        submissions = ModelSubmission.objects.filter(title__icontains=query)
    else:
        submissions = ModelSubmission.objects.all()

    context = {
        'submissions': submissions,
        'total_count': submissions.count(),
    }
    return render(request, 'acatalog.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def model_delete_view(request, pk):
    # Находим модель или выдаем 404
    submission = get_object_or_404(ModelSubmission, pk=pk)
    # Удаляем ее
    submission.delete()
    # Возвращаемся обратно в каталог
    return redirect('acatalog')


@login_required
def security_view(request):
    # Просто отдаем твою страницу с щитом
    return render(request, 'security.html')

@login_required
def password_change_view(request):
    if request.method == 'POST':
        # Передаем request.user первым аргументом, данные из POST — вторым
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Важно: обновляем сессию, чтобы юзера не выкинуло
            update_session_auth_hash(request, user)
            
            # Обновляем дату изменения в профиле (если поле создано)
            if hasattr(request.user, 'profile'):
                request.user.profile.password_changed_at = timezone.now()
                request.user.profile.save()
                
            messages.success(request, "Пароль успешно изменен!")
            return redirect('security')
    else:
        # Теперь форма будет видна и при GET запросе
        form = PasswordChangeForm(request.user)
        
    return render(request, 'password_change_form.html', {'form': form})

@login_required
def profile_view(request):
    if request.user.is_superuser:
        # Логика для админа
        return render(request, 'profile_admin.html')
    else:
        # 1. Получаем избранные модели
        favorite_models = request.user.profile.favorite_models.all()
        
        # 2. Считаем количество УНИКАЛЬНЫХ скачанных изделий пользователем
        # .values('model_item') сгруппирует логи по моделям, .distinct() уберет повторы
        downloaded_count = DownloadLog.objects.filter(user=request.user).count()
        # downloaded_count = DownloadLog.objects.filter(user=request.user).values('model_item').distinct().count()
        
        context = {
            'favorite_models': favorite_models,
            'fav_count': favorite_models.count(),
            'downloaded_count': downloaded_count,
            # last_login уже есть в объекте user по умолчанию
        }
        return render(request, 'profile_user.html', context)


def download_file(request, pk, file_format):
    model_item = get_object_or_404(ModelSubmission, pk=pk)
    
    # 1. Получаем IP адрес (для истории)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    # 2. Создаем запись в логах
    DownloadLog.objects.create(
        model_item=model_item,
        user=request.user if request.user.is_authenticated else None,
        file_format=file_format.upper(),
        ip_address=ip
    )

    # 3. Увеличиваем общий счетчик в основной модели
    ModelSubmission.objects.filter(pk=pk).update(download_count=F('download_count') + 1)

    # 4. Редирект на сам файл
    file_field = getattr(model_item, f'file_{file_format.lower()}', None)
    if file_field:
        return redirect(file_field.url)
    
    return redirect('model_detail', pk=pk)


@login_required
@require_POST
def toggle_favorite(request, model_id):
    model_item = get_object_or_404(ModelSubmission, id=model_id)
    profile = request.user.profile
    
    if model_item in profile.favorite_models.all():
        profile.favorite_models.remove(model_item)
        action = 'removed'
    else:
        profile.favorite_models.add(model_item)
        action = 'added'
        
    return JsonResponse({'status': 'ok', 'action': action})


@user_passes_test(lambda u: u.is_superuser)
def admin_profile_view(request):
    # Собираем реальные цифры из базы
    context = {
        'users_count': User.objects.count(),
        'models_count': ModelSubmission.objects.count(),
        'news_count': NewsItem.objects.count(),
        'docs_count': 6,  # Если будет модель документов, замени на .count()
        
        # Топ изделий по скачиванию
        'top_models': ModelSubmission.objects.order_by('-download_count')[:5],
        
        # Последние действия (скачивания)
        'recent_actions': DownloadLog.objects.select_related('user', 'model_item').order_by('-timestamp')[:5]
    }
    return render(request, 'profile_admin.html', context)




@login_required
def chat_stub_view(request):
    # Если это админ, можно передать другой заголовок
    is_admin = request.user.is_superuser
    return render(request, 'chat_stub.html', {'is_admin': is_admin})


@login_required
def chat_list(request):
    if request.user.is_staff:
        # 1. Проверяем, есть ли непрочитанные сообщения от клиентов для индикатора в меню
        has_unread = ChatMessage.objects.filter(is_read=False).exclude(sender__is_staff=True).exists()

        # 2. Получаем список всех комнат с последним временем сообщения
        rooms = ChatRoom.objects.select_related('user', 'user__profile').annotate(
            last_msg_time=Max('messages__created_at')
        ).order_by('-last_msg_time')

        return render(request, 'chat/chat_list.html', {
            'rooms': rooms,
            'has_unread': has_unread  # Передаем статус непрочитанных
        })

    # ДЛЯ КЛИЕНТА: Перенаправляем в его единственный чат
    room, created = ChatRoom.objects.get_or_create(user=request.user)
    return redirect('chat_room', room_id=room.id)


@login_required
def chat_room_view(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Защита: клиент может зайти только в СВОЙ чат. Админ может в любой.
    if not request.user.is_staff and room.user != request.user:
        return redirect('home')

    # ПОМЕТКА ПРОЧИТАННЫМ:
    # Когда кто-то открывает чат, все сообщения в этой комнате, 
    # отправленные НЕ этим пользователем, становятся прочитанными.
    room.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

    if request.method == 'POST':
        body = request.POST.get('message', '').strip()
        file = request.FILES.get('file') # Получаем файл из запроса

        # Создаем сообщение, если есть текст ИЛИ файл
        if body or file:
            ChatMessage.objects.create(
                room=room,
                sender=request.user,
                body=body,
                file=file
            )
            
            # Если это AJAX запрос (от Drag-and-Drop или JS), возвращаем пустой ответ или статус
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return redirect('chat_room', room_id=room.id)
            
            return redirect('chat_room', room_id=room.id)

    # Оптимизированная загрузка сообщений
    chat_messages = room.messages.select_related('sender', 'sender__profile').all().order_by('created_at')
    
    return render(request, 'chat/chat_room.html', {
        'room': room,
        'chat_messages': chat_messages
    })