from datetime import date

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.admin.views.decorators import staff_member_required

from blog.models import Category, Post
from .forms import RegistrationForm, PostForm, ProfileEditForm, CommentForm, AvatarForm
from .models import Comment, Profile

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
        .annotate(comment_count=Count('comments'))
        .order_by('-is_pinned', '-pub_date') 
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
    ).select_related("category", "location", "author").annotate(
        comment_count=Count('comments')
    ).order_by('-is_pinned', '-pub_date')  
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "category": category,
    }
    return render(request, "blog/category.html", context)


def post_detail(request, id):
    post = get_object_or_404(Post, id=id)
    today = date.today()
    if (not post.is_published 
            or post.pub_date.date() > today 
            or not post.category.is_published):
        if request.user != post.author:
            raise Http404("Пост не найден")
    comments = post.comments.all()
    form = CommentForm()
    context = {"post": post, "comments": comments, "form": form}
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

    posts = posts.order_by('-is_pinned', '-pub_date').annotate(comment_count=Count('comments'))

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


@staff_member_required
def toggle_pin(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_pinned = not post.is_pinned
    post.save()
    return redirect(request.META.get('HTTP_REFERER', 'blog:index'))

# ---------- Редактирование профиля ----------

@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = ProfileEditForm(request.POST, instance=request.user)
        avatar_form = AvatarForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and avatar_form.is_valid():
            user_form.save()
            avatar_form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        user_form = ProfileEditForm(instance=request.user)
        avatar_form = AvatarForm(instance=profile)
    return render(request, 'blog/edit_profile.html', {'user_form': user_form, 'avatar_form': avatar_form})


# ---------- Комментарии ----------

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})