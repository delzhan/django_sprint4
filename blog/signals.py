from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import PostLike, CommentLike, Comment, Notification


@receiver(post_save, sender=PostLike)
def create_post_like_notification(sender, instance, created, **kwargs):
    if not created:
        return
    post = instance.post
    author = post.author
    if author != instance.user:
        Notification.objects.create(
            user=author,
            type=Notification.Type.LIKE_POST,
            text=f'{instance.user.username} лайкнул ваш пост "{post.title[:50]}"',
            link=reverse('post_detail', args=[post.id])
        )


@receiver(post_save, sender=CommentLike)
def create_comment_like_notification(sender, instance, created, **kwargs):
    if not created:
        return
    comment = instance.comment
    author = comment.author
    if author != instance.user:
        Notification.objects.create(
            user=author,
            type=Notification.Type.LIKE_COMMENT,
            text=f'{instance.user.username} лайкнул ваш комментарий',
            link=reverse('post_detail', args=[comment.post.id]) + f'#comment-{comment.id}'
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return
    post = instance.post
    author = post.author
    if author != instance.author:
        Notification.objects.create(
            user=author,
            type=Notification.Type.NEW_COMMENT,
            text=f'{instance.author.username} прокомментировал ваш пост "{post.title[:50]}"',
            link=reverse('post_detail', args=[post.id]) + f'#comment-{instance.id}'
        )