from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Post, Category, Location, Comment, Profile

User = get_user_model()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
        }


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'location', 'category', 'is_published', 'image')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Категории: только опубликованные, по алфавиту, с пустой опцией
        self.fields['category'].queryset = Category.objects.filter(is_published=True).order_by('title')
        self.fields['category'].empty_label = 'Выберите категорию'
        # Местоположения: только опубликованные, по алфавиту, с пустой опцией
        self.fields['location'].queryset = Location.objects.filter(is_published=True).order_by('name')
        self.fields['location'].empty_label = 'Выберите местоположение'


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class AvatarForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar',)