import json
from datetime import date

from django.contrib.auth import get_user_model, login
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Q, Value, BooleanField, F
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from blog.models import Category, Post
from .forms import RegistrationForm, PostForm, ProfileEditForm, CommentForm, AvatarForm
from .models import Comment, Profile, PostLike, CommentLike, Notification

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

    # Аннотируем is_liked для авторизованных пользователей
    if request.user.is_authenticated:
        post_list = post_list.annotate(
            is_liked=Exists(PostLike.objects.filter(user=request.user, post=OuterRef('pk')))
        )
    else:
        post_list = post_list.annotate(is_liked=Value(False, output_field=BooleanField()))

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

    if request.user.is_authenticated:
        post_list = post_list.annotate(
            is_liked=Exists(PostLike.objects.filter(user=request.user, post=OuterRef('pk')))
        )
    else:
        post_list = post_list.annotate(is_liked=Value(False, output_field=BooleanField()))

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

    if request.user.is_authenticated:
        post.is_liked = PostLike.objects.filter(user=request.user, post=post).exists()
    else:
        post.is_liked = False

    # Комментарии с аннотацией is_liked
    comments = post.comments.all()
    if request.user.is_authenticated:
        comments = comments.annotate(
            is_liked=Exists(CommentLike.objects.filter(user=request.user, comment=OuterRef('pk')))
        )
    else:
        comments = comments.annotate(is_liked=Value(False, output_field=BooleanField()))

    form = CommentForm()
    context = {"post": post, "comments": comments, "form": form}
    return render(request, "blog/detail.html", context)


def page_not_found(request, exception):
    return render(request, "pages/404.html", status=404)


def csrf_failure(request, reason=""):
    return render(request, "pages/403csrf.html", status=403)


def server_error(request):
    return render(request, "pages/500.html", status=500)


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

    posts = posts.order_by('-is_pinned', '-pub_date').annotate(comment_count=Count('comments'))

    if request.user.is_authenticated:
        posts = posts.annotate(
            is_liked=Exists(PostLike.objects.filter(user=request.user, post=OuterRef('pk')))
        )
    else:
        posts = posts.annotate(is_liked=Value(False, output_field=BooleanField()))

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    user_profile = profile_user.profile

    context = {
        "profile_user": profile_user,
        "profile": user_profile,
        "page_obj": page_obj,
    }
    return render(request, "blog/profile.html", context)


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


@login_required
def toggle_post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like = PostLike.objects.filter(user=request.user, post=post)

    if like.exists():
        like.delete()
        liked = False
    else:
        PostLike.objects.create(user=request.user, post=post)
        liked = True

    post.likes_count = post.likes.count()
    post.save(update_fields=['likes_count'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': post.likes_count,
        })
    return redirect(request.META.get('HTTP_REFERER', 'blog:post_detail'))


@login_required
def toggle_comment_like(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    like = CommentLike.objects.filter(user=request.user, comment=comment)

    if like.exists():
        like.delete()
        liked = False
    else:
        CommentLike.objects.create(user=request.user, comment=comment)
        liked = True

    comment.likes_count = comment.likes.count()
    comment.save(update_fields=['likes_count'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': comment.likes_count,
        })
    return redirect(request.META.get('HTTP_REFERER', 'blog:post_detail'))


@login_required
def notifications(request):
    all_notifications = request.user.notifications.all()
    unread = all_notifications.filter(is_read=False)

    show_unread = request.GET.get('filter') == 'unread'
    if show_unread:
        notif_list = unread
    else:
        notif_list = all_notifications

    context = {
        'notifications': notif_list,
        'unread_count': unread.count(),
        'show_unread': show_unread,
    }
    return render(request, 'blog/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('blog:notifications')


@login_required
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('blog:notifications')