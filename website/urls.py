# website/urls.py

from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ── Обычные страницы ──────────────────────────────────────
    path('',                 views.home,           name='home'),
    path('contacts/',        views.contacts,       name='contacts'),
    path('news/',            views.news_list_view, name='news'),
    path('news/<int:pk>/', views.news_detail_view, name='news_detail'),
    path('catalog/',         views.catalog,        name='catalog'),
    path('catalog/<int:pk>/', views.model_detail,  name='model_detail'),   # ← НОВЫЙ
    path('documentation/',   views.documentation,  name='documentation'),
    path('about_platform/',  views.about_platform, name='about_platform'),
    path('questions/',       views.questions,      name='questions'),

    # ── Авторизация ───────────────────────────────────────────
    path('login/',    views.login_view,   name='login'),
    path('logout/',   views.logout_user,  name='logout'),
    path('signup/',   views.signup_view,  name='signup'),

    # ── Сброс пароля ─────────────────────────────────────────
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        html_email_template_name='password_reset_email.html',
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html',
    ), name='password_reset_complete'),

    # ── Чат ──────────────────────────────────────────────────


    # ── Профиль ─────────────────────────────────────────────
    path('settings/',  views.settings_view, name='settings'),
    path('anews/', views.anews_view, name='anews'),
    path('anews/create/', views.create_news_view, name='create_news'),
    path('anews/edit/<int:pk>/', views.edit_news_view, name='edit_news'),
    path('anews/delete/<int:pk>/', views.delete_news_view, name='delete_news'),


    path('adocumentation/', views.adocumentation_view, name='adocumentation'),
    path('adocumentation/add/', views.document_edit_view, name='add_document'),
    path('adocumentation/edit/<int:pk>/', views.document_edit_view, name='edit_document'),
    path('adocumentation/delete/<int:pk>/', views.delete_document_view, name='delete_document'),

    path('acatalog/', views.acatalog_view, name='acatalog'),
    path('acatalog/add/', views.model_edit_view, name='add_model'),
    path('acatalog/edit/<int:pk>/', views.model_edit_view, name='edit_model'),
    path('acatalog/delete/<int:pk>/', views.model_delete_view, name='delete_model'),

    # Страница "Безопасность"
    path('security/', views.security_view, name='security'),
    path('security/change-password/', views.password_change_view, name='password_change'),

    path('profile/', views.profile_view, name='profile'),
    path('download/<int:pk>/<str:file_format>/', views.download_file, name='download_file'),

    path('chat/', views.chat_list, name='chat'),
    path('chat/<int:room_id>/', views.chat_room_view, name='chat_room'),
    
    path('favorite/toggle/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
]