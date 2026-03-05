# website/views.py

import os
from time import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from website.models import ModelSubmission, NewsItem, Profile, Document
from .forms import DocumentForm, UserUpdateForm, ProfileUpdateForm, ModelSubmissionForm
from .forms import SignUpForm


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

from django.db.models import Q
from django.core.paginator import Paginator

from django.shortcuts import render
from django.db.models import Q
from .models import ModelSubmission


def catalog(request):
    # Убрали фильтр по статусу APPROVED, чтобы увидеть всё, что есть в БД
    models_queryset = ModelSubmission.objects.all()

    # Поиск
    query = request.GET.get('q')
    if query:
        models_queryset = models_queryset.filter(
            Q(title__icontains=query) | Q(standard__icontains=query)
        )

    # Фильтр по форматам
    selected_formats = request.GET.getlist('formats')
    if 'STEP' in selected_formats:
        models_queryset = models_queryset.filter(file_stp__icontains='') # Проверка на наличие файла
    if 'STL' in selected_formats:
        models_queryset = models_queryset.filter(file_stl__icontains='')
    if 'IGES' in selected_formats:
        models_queryset = models_queryset.filter(file_igs__icontains='')

    context = {
        'models': models_queryset,
        'query': query,
        'selected_formats': selected_formats,
    }
    return render(request, 'catalog.html', context)

def model_detail(request, pk):
    # Деталка (чтобы URL не падал с ошибкой)
    model_item = get_object_or_404(ModelSubmission, pk=pk)
    return render(request, 'model_detail.html', {'model': model_item})

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
            messages.error(request, "Неверный Email или пароль")
            return render(request, 'login.html')
    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request):
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
def acatalog_view(request):
    query = request.GET.get('q')
    
    # Берем все модели, КРОМЕ отклоненных
    submissions = ModelSubmission.objects.exclude(status=ModelSubmission.STATUS_REJECTED)
    
    # Если есть поисковый запрос, фильтруем отфильтрованный список
    if query:
        submissions = submissions.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
        
    return render(request, 'acatalog.html', {
        'submissions': submissions,
        'total_count': submissions.count()
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def acatalog_view(request):
    query = request.GET.get('q')
    # Исключаем отклоненные
    submissions = ModelSubmission.objects.exclude(status=ModelSubmission.STATUS_REJECTED)
    
    if query:
        submissions = submissions.filter(Q(title__icontains=query))
        
    return render(request, 'acatalog.html', {
        'submissions': submissions,
        'total_count': submissions.count()
    })


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


def model_detail(request, pk):
    """Отображение страницы конкретной модели"""
    model_item = get_object_or_404(ModelSubmission, pk=pk, status=ModelSubmission.STATUS_APPROVED)
    
    context = {
        'model': model_item,
    }
    return render(request, 'model_detail.html', context)