from django import forms
from post.models import Post
from .models import Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['post_story', 'author']

from django import forms


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('author', 'text')
