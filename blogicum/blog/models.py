from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Category(models.Model):
    title = models.CharField(max_length=256, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    slug = models.SlugField(
        unique=True,
        verbose_name="Идентификатор",
        help_text="Идентификатор страницы для URL; разрешены символы латиницы, цифры, дефис и подчёркивание.",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено",
    )

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.title


class Location(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name="Название места",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено",
    )

    class Meta:
        verbose_name = "местоположение"
        verbose_name_plural = "Местоположения"
        
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=256, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст")
    pub_date = models.DateTimeField(
        verbose_name="Дата и время публикации",
        help_text="Если установить дату и время в будущем — можно делать отложенные публикации.",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор публикации",
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Местоположение",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Категория",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено",
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images/',
        blank=True,
        null=True,
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='Закреплённый пост',
        help_text='Отметьте, чтобы пост отображался первым в ленте.',
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество лайков'
    )

    class Meta:
        verbose_name = "публикация"
        verbose_name_plural = "Публикации"


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество лайков'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'


class PostLike(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='post_likes',
        verbose_name='Пользователь'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Пост'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        unique_together = ('user', 'post')
        verbose_name = 'лайк поста'
        verbose_name_plural = 'Лайки постов'

    def __str__(self):
        return f'{self.user} лайкнул {self.post}'


class CommentLike(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comment_likes',
        verbose_name='Пользователь'
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Комментарий'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        unique_together = ('user', 'comment')
        verbose_name = 'лайк комментария'
        verbose_name_plural = 'Лайки комментариев'

    def __str__(self):
        return f'{self.user} лайкнул комментарий {self.comment.id}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f'Профиль {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()