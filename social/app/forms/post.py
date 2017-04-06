import base64

from django import forms

from social.app.models.category import Category
from social.app.models.post import Post


class PostForm(forms.ModelForm):
    categories = forms.CharField(
        label="Categories",
        required=False,
        help_text="Space-delimited",
    )

    content_type = forms.ChoiceField(choices=Post.TEXT_CONTENT_TYPES)

    upload_content_type = forms.ChoiceField(
        choices=[("", "")] + Post.IMAGE_CONTENT_TYPES,
        required=False
    )

    upload_content = forms.FileField(
        required=False
    )

    def save(self, commit=True, *args, **kwargs):
        request = kwargs["request"]

        instance = super(PostForm, self).save(commit=False)

        instance.author = request.user.profile

        if not (instance.source and instance.origin):
            # Source:
            # https://docs.djangoproject.com/en/1.10/ref/request-response/#django.http.HttpRequest.build_absolute_uri
            url = request.build_absolute_uri(instance.get_absolute_url())

            instance.source = url
            instance.origin = url

        self.save_categories(instance, commit)

        if 'upload_content' in self.files:
            file_content = self.files['upload_content']
            if instance.child_post is None:
                instance.child_post = Post(
                    author=instance.author,
                    title="Upload",
                    description="Upload",
                    source=instance.source,
                    origin=instance.origin,
                    unlisted=instance.unlisted,
                    visibility=instance.visibility,
                    visible_to=instance.visible_to.all(),
                    categories=instance.categories.all()
                )

                instance.child_post.content_type = self.cleaned_data["upload_content_type"]
                instance.child_post.content = base64.b64encode(file_content.read())

        if commit:
            instance.save()
            self.save_m2m()

            if instance.child_post:
                instance.child_post.save()

        return instance

    def save_categories(self, instance, commit=True):
        categories_string = self.cleaned_data["categories"]
        if categories_string:
            for name in categories_string.split(" "):
                if not instance.categories.filter(name=name).exists():
                    category = Category.objects.filter(name=name).first()

                    if category is None:
                        category = Category.objects.create(name=name)

                    instance.categories.add(category)

    # Source:
    # https://docs.djangoproject.com/en/1.10/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
    def clean(self):
        cleaned_data = super(PostForm, self).clean()
        upload_content = cleaned_data["upload_content"]
        upload_content_type = cleaned_data["upload_content_type"]

        # upload_content and type must either both be set or both not be set
        if (upload_content and not upload_content_type) or (not upload_content and upload_content_type):
            raise forms.ValidationError("Upload content type can only be set if a file is uploaded, and vice-versa.")

    class Meta:
        model = Post
        fields = ["title", "description", "content_type", "content", "visibility", "visible_to",
                  "unlisted"]
