from datetime import date

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from blog.models import Category, Post
from .forms import RegistrationForm, PostForm, ProfileEditForm

User = get_user_model()


def index(request):
    today = date.today()
    post_list = (
        Post.objects.select_related("category")
        .filter(
            is_published=True,
            pub_date__lte=today,
            category__is_published=True,
        )
        .select_related("category", "location", "author")
        .order_by("-pub_date")
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return render(request, "blog/index.html", context)


def category_posts(request, category_slug):
    today = date.today()
    category = get_object_or_404(
        Category,
        Q(slug=category_slug) & Q(is_published=True),
    )
    post_list = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=today,
    ).select_related("category", "location", "author")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "category": category,
    }
    return render(request, "blog/category.html", context)


def post_detail(request, id):
    today = date.today()
    post = get_object_or_404(
        Post,
        Q(id=id)
        & Q(is_published=True)
        & Q(pub_date__lte=today)
        & Q(category__is_published=True),
    )
    context = {"post": post}
    return render(request, "blog/detail.html", context)


# ---------- Кастомные страницы ошибок ----------

def page_not_found(request, exception):
    return render(request, "pages/404.html", status=404)


def csrf_failure(request, reason=""):
    return render(request, "pages/403csrf.html", status=403)


def server_error(request):
    return render(request, "pages/500.html", status=500)


# ---------- Работа с пользователями ----------

def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("blog:profile", username=user.username)
    else:
        form = RegistrationForm()
    return render(request, "registration/registration_form.html", {"form": form})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    today = date.today()

    posts = Post.objects.filter(author=profile_user).select_related(
        "category", "location", "author"
    )

    if request.user != profile_user:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=today,
            category__is_published=True,
        )
    else:
        posts = posts.filter(category__is_published=True)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "profile": profile_user,
        "page_obj": page_obj,
    }
    return render(request, "blog/profile.html", context)


# ---------- Работа с публикациями ----------

@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("blog:profile", username=request.user.username)
    else:
        form = PostForm()
    return render(request, "blog/create.html", {"form": form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("blog:post_detail", id=post_id)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect("blog:post_detail", id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, "blog/create.html", {"form": form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("blog:post_detail", id=post_id)
    if request.method == "POST":
        post.delete()
        return redirect("blog:profile", username=request.user.username)
    return render(request, "blog/create.html", {"form": post})


# ---------- Редактирование профиля ----------

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("blog:profile", username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "blog/edit_profile.html", {"form": form})