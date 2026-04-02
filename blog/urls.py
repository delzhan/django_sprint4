from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.index, name="index"),
    path("posts/<int:id>/", views.post_detail, name="post_detail"),
    path("category/<slug:category_slug>/", views.category_posts, name="category_posts"),
    path("auth/registration/", views.registration, name="registration"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path("posts/create/", views.create_post, name="create_post"),
    path("posts/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("posts/<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("posts/<int:post_id>/comment/", views.add_comment, name="add_comment"),
    path("posts/<int:post_id>/edit_comment/<int:comment_id>/", views.edit_comment, name="edit_comment"),
    path("posts/<int:post_id>/delete_comment/<int:comment_id>/", views.delete_comment, name="delete_comment"),
    path('posts/<int:post_id>/toggle_pin/', views.toggle_pin, name='toggle_pin'),
    path('posts/<int:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('posts/<int:post_id>/comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_read, name='mark_all_read'),
]