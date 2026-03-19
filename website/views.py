import os
from django.utils import timezone
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


def superuser_required(user):
    return user.is_superuser


def home(request):
    return render(request, "index.html")


def contacts(request):
    return render(request, "contacts.html")


def news_list_view(request):
    news = NewsItem.objects.all()
    return render(request, "news.html", {"news_list": news})


def news_detail_view(request, pk):
    news_item = get_object_or_404(NewsItem, pk=pk)

    news_item.views_count += 1
    news_item.save()

    return render(request, "news_detail.html", {"item": news_item})


def documentation(request):
    documents = Document.objects.all().order_by("standard_number")
    return render(request, "documentation.html", {"documents": documents})


def adocumentation_view(request):

    query = request.GET.get("q")

    if query:

        documents = Document.objects.filter(
            name__icontains=query
        ) | Document.objects.filter(standard_number__icontains=query)
    else:
        documents = Document.objects.all()

    return render(request, "adocumentation.html", {"documents": documents})


def document_edit_view(request, pk=None):

    instance = get_object_or_404(Document, pk=pk) if pk else None

    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("adocumentation")
    else:
        form = DocumentForm(instance=instance)

    return render(
        request, "document_form.html", {"form": form, "edit_mode": pk is not None}
    )


def about_platform(request):
    return render(request, "about_platform.html")


def questions(request):
    return render(request, "questions.html")


def catalog(request):

    models_queryset = ModelSubmission.objects.all()

    query = request.GET.get("q")
    if query:
        models_queryset = models_queryset.filter(
            Q(title__icontains=query) | Q(standard__icontains=query)
        )

    selected_formats = request.GET.getlist("formats")
    if selected_formats:
        format_queries = Q()
        if "STEP" in selected_formats:

            format_queries |= Q(file_stp__isnull=False) & ~Q(file_stp="")
        if "STL" in selected_formats:
            format_queries |= Q(file_stl__isnull=False) & ~Q(file_stl="")
        if "IGES" in selected_formats:
            format_queries |= Q(file_igs__isnull=False) & ~Q(file_igs="")

        models_queryset = models_queryset.filter(format_queries)

    context = {
        "models": models_queryset,
        "query": query,
        "selected_formats": selected_formats,
    }
    return render(request, "catalog.html", context)


def model_detail(request, pk):

    submission = get_object_or_404(ModelSubmission, pk=pk)

    related = ModelSubmission.objects.filter(category=submission.category).exclude(
        pk=pk
    )[:4]

    return render(
        request, "model_detail.html", {"submission": submission, "related": related}
    )


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Регистрация прошла успешно! Теперь войдите.")
            return redirect("login")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect("settings")
        else:

            return render(request, "login.html", {"error": "Неверный Email или пароль"})
    return render(request, "login.html")


def logout_user(request):
    logout(request)
    return redirect("/")


@login_required
def settings_view(request):
    is_edit = request.GET.get("edit") == "1"

    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect("settings")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    if not is_edit:
        for field in u_form.fields.values():
            field.widget.attrs["disabled"] = "disabled"
        for field in p_form.fields.values():
            field.widget.attrs["disabled"] = "disabled"

    return render(
        request,
        "settings.html",
        {"u_form": u_form, "p_form": p_form, "is_edit": is_edit},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def anews_view(request):
    query = request.GET.get("q")
    if query:

        news_items = NewsItem.objects.filter(title__icontains=query)
    else:
        news_items = NewsItem.objects.all()

    return render(request, "anews.html", {"news_items": news_items})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_news_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        image = request.FILES.get("image")

        if title:
            NewsItem.objects.create(title=title, content=content, image=image)
            return redirect("anews")

    return render(request, "create_news.html", {"is_edit": False})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_news_view(request, pk):
    news = get_object_or_404(NewsItem, pk=pk)
    if request.method == "POST":
        news.title = request.POST.get("title")
        news.content = request.POST.get("content")
        if request.FILES.get("image"):
            news.image = request.FILES.get("image")
        news.save()
        return redirect("anews")

    return render(request, "create_news.html", {"news": news, "is_edit": True})


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_news_view(request, pk):
    news = get_object_or_404(NewsItem, pk=pk)
    news.delete()
    return redirect("anews")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def model_edit_view(request, pk=None):
    instance = get_object_or_404(ModelSubmission, pk=pk) if pk else None

    if request.method == "POST":
        form = ModelSubmissionForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("acatalog")
    else:
        form = ModelSubmissionForm(instance=instance)

    file_fields = []
    fields_info = [("file_stp", "STP"), ("file_igs", "IGS"), ("file_stl", "STL")]

    for field_name, ext in fields_info:
        file_obj = getattr(instance, field_name) if instance else None
        if file_obj and hasattr(file_obj, "url"):

            file_url = file_obj.url
            file_basename = os.path.basename(file_obj.name)
        else:

            file_url = None
            file_basename = None

        file_fields.append((field_name, ext, file_url, file_basename))

    return render(
        request,
        "amanage_model.html",
        {
            "form": form,
            "edit_mode": pk is not None,
            "instance": instance,
            "file_fields": file_fields,
        },
    )


def acatalog_view(request):

    query = request.GET.get("q", "")
    if query:
        submissions = ModelSubmission.objects.filter(title__icontains=query)
    else:
        submissions = ModelSubmission.objects.all()

    context = {
        "submissions": submissions,
        "total_count": submissions.count(),
    }
    return render(request, "acatalog.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def model_delete_view(request, pk):

    submission = get_object_or_404(ModelSubmission, pk=pk)

    submission.delete()

    return redirect("acatalog")


@login_required
def security_view(request):

    return render(request, "security.html")


@login_required
def password_change_view(request):
    if request.method == "POST":

        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()

            update_session_auth_hash(request, user)

            if hasattr(request.user, "profile"):
                request.user.profile.password_changed_at = timezone.now()
                request.user.profile.save()

            messages.success(request, "Пароль успешно изменен!")
            return redirect("security")
    else:

        form = PasswordChangeForm(request.user)

    return render(request, "password_change_form.html", {"form": form})


@login_required
def profile_view(request):
    if request.user.is_superuser:

        users_count = User.objects.count()
        models_count = ModelSubmission.objects.count()
        docs_count = Document.objects.count()
        news_count = NewsItem.objects.count()

        top_models = ModelSubmission.objects.order_by("-download_count")[:5]

        recent_actions = DownloadLog.objects.select_related(
            "user", "model_item"
        ).order_by("-timestamp")[:5]

        context = {
            "users_count": users_count,
            "models_count": models_count,
            "docs_count": docs_count,
            "news_count": news_count,
            "top_models": top_models,
            "recent_actions": recent_actions,
        }
        return render(request, "profile_admin.html", context)
    else:

        favorite_models = request.user.profile.favorite_models.all()

        downloaded_count = DownloadLog.objects.filter(user=request.user).count()

        context = {
            "favorite_models": favorite_models,
            "fav_count": favorite_models.count(),
            "downloaded_count": downloaded_count,
        }
        return render(request, "profile_user.html", context)


def download_file(request, pk, file_format):
    model_item = get_object_or_404(ModelSubmission, pk=pk)

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    DownloadLog.objects.create(
        model_item=model_item,
        user=request.user if request.user.is_authenticated else None,
        file_format=file_format.upper(),
        ip_address=ip,
    )

    ModelSubmission.objects.filter(pk=pk).update(download_count=F("download_count") + 1)

    file_field = getattr(model_item, f"file_{file_format.lower()}", None)
    if file_field:
        return redirect(file_field.url)

    return redirect("model_detail", pk=pk)


@login_required
@require_POST
def toggle_favorite(request, model_id):
    model_item = get_object_or_404(ModelSubmission, id=model_id)
    profile = request.user.profile

    if model_item in profile.favorite_models.all():
        profile.favorite_models.remove(model_item)
        action = "removed"
    else:
        profile.favorite_models.add(model_item)
        action = "added"

    return JsonResponse({"status": "ok", "action": action})


@user_passes_test(lambda u: u.is_superuser)
def admin_profile_view(request):

    context = {
        "users_count": User.objects.count(),
        "models_count": ModelSubmission.objects.count(),
        "news_count": NewsItem.objects.count(),
        "docs_count": 6,
        "top_models": ModelSubmission.objects.order_by("-download_count")[:5],
        "recent_actions": DownloadLog.objects.select_related(
            "user", "model_item"
        ).order_by("-timestamp")[:5],
    }
    return render(request, "profile_admin.html", context)


@login_required
def chat_stub_view(request):

    is_admin = request.user.is_superuser
    return render(request, "chat_stub.html", {"is_admin": is_admin})


@login_required
def chat_list(request):
    if request.user.is_staff:

        has_unread = (
            ChatMessage.objects.filter(is_read=False)
            .exclude(sender__is_staff=True)
            .exists()
        )

        rooms = (
            ChatRoom.objects.select_related("user", "user__profile")
            .annotate(last_msg_time=Max("messages__created_at"))
            .order_by("-last_msg_time")
        )

        return render(
            request, "chat/chat_list.html", {"rooms": rooms, "has_unread": has_unread}
        )

    room, created = ChatRoom.objects.get_or_create(user=request.user)
    return redirect("chat_room", room_id=room.id)


@login_required
def chat_room_view(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    if not request.user.is_staff and room.user != request.user:
        return redirect("home")

    room.messages.exclude(sender=request.user).filter(is_read=False).update(
        is_read=True
    )

    if request.method == "POST":
        body = request.POST.get("message", "").strip()
        file = request.FILES.get("file")

        if body or file:
            ChatMessage.objects.create(
                room=room, sender=request.user, body=body, file=file
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return redirect("chat_room", room_id=room.id)

            return redirect("chat_room", room_id=room.id)

    chat_messages = (
        room.messages.select_related("sender", "sender__profile")
        .all()
        .order_by("created_at")
    )

    return render(
        request, "chat/chat_room.html", {"room": room, "chat_messages": chat_messages}
    )


@login_required
def toggle_favorite(request, pk):
    model_obj = get_object_or_404(ModelSubmission, pk=pk)
    profile = request.user.profile

    if model_obj in profile.favorite_models.all():
        profile.favorite_models.remove(model_obj)
        is_favorite = False
    else:
        profile.favorite_models.add(model_obj)
        is_favorite = True

    return JsonResponse(
        {
            "status": "ok",
            "is_favorite": is_favorite,
            "count": profile.favorite_models.count(),
        }
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_document_view(request, pk):

    document = get_object_or_404(Document, pk=pk)

    if document.file:
        if os.path.isfile(document.file.path):
            os.remove(document.file.path)

    document.delete()

    return redirect("adocumentation")


@login_required
@require_POST
def delete_avatar_view(request):
    profile = request.user.profile
    if profile.avatar:
        profile.avatar.delete()
        profile.avatar = None
        profile.save()
    return JsonResponse({"status": "success"})