import base64
import uuid
from abc import ABCMeta

from django import forms

from social.app.models.category import Category
from social.app.models.post import Post

"""
Overriding ModelForm.save idea from Wogan (http://stackoverflow.com/users/137902/wogan) on StackOverflow
Link: http://stackoverflow.com/a/3929671 (CC-BY-SA 3.0)
"""


class PostFormBase(forms.ModelForm):
    categories = forms.CharField(
        label="Categories",
        required=False,
        help_text="Space-delimited",
    )

    def save(self, commit=True, *args, **kwargs):
        request = kwargs["request"]
        current_author = request.user.profile
        new_id = uuid.uuid4()

        instance = super(PostFormBase, self).save(commit=False)

        instance.id = new_id
        instance.author = current_author

        # Source:
        # https://docs.djangoproject.com/en/1.10/ref/request-response/#django.http.HttpRequest.build_absolute_uri
        url = request.build_absolute_uri(instance.get_absolute_url())

        instance.source = url
        instance.origin = url

        self.save_categories(instance, commit)
        self.save_hook(instance, request)

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    def save_categories(self, instance, commit=True):
        categories_string = self.cleaned_data["categories"]
        if categories_string:
            for name in categories_string.split(" "):
                if not instance.categories.filter(name=name).exists():
                    category = Category.objects.filter(name=name).first()

                    if category is None:
                        category = Category(name=name)
                        if commit:
                            category.save()

                    instance.categories.add(category)

    def save_hook(self, instance, request):
        """
        Redefine this in the child class.
        """
        pass


class TextPostForm(PostFormBase):
    content_type = forms.ChoiceField(choices=Post.TEXT_CONTENT_TYPES)
    categories = forms.CharField(
        label="Categories",
        required=False,
        help_text="Space-delimited",
    )

    class Meta:
        model = Post
        fields = ["title", "description", "content_type", "content", "visibility", "visible_to",
                  "unlisted"]


class FilePostForm(PostFormBase):
    content_type = forms.ChoiceField(choices=Post.UPLOAD_CONTENT_TYPES)
    content = forms.FileField()

    class Meta:
        model = Post
        fields = ["title", "description", "content_type", "content", "visibility", "visible_to"]

    def save_hook(self, instance, request):
        file_content = request.FILES['content']
        instance.content = base64.b64encode(file_content.read())

        # Upload posts are always unlisted
        instance.unlisted = True
