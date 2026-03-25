from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Profile, Post, Category, Location, Comment

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Остальные модели
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)