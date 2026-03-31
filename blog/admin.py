from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Profile, Post, Category, Location, Comment, PostLike, CommentLike

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'pub_date', 'is_published', 'likes_count', 'is_pinned')
    list_filter = ('is_published', 'category', 'pub_date')
    search_fields = ('title', 'author__username')
    readonly_fields = ('likes_count',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at', 'likes_count')
    list_filter = ('created_at',)
    search_fields = ('text', 'author__username')
    readonly_fields = ('likes_count',)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'comment__text')


# Стандартные регистрации для остальных моделей
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Category)
admin.site.register(Location)