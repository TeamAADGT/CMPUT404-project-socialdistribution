import base64, uuid

from django import forms

from social.app.models.category import Category
from social.app.models.post import Post
from social.app.models.author import Author


class PostForm(forms.ModelForm):
    categories = forms.CharField(
        label="Categories",
        required=False,
        help_text="Space-delimited",
    )

    visible_to = forms.CharField(
        label="Visible to",
        required=False,
        help_text="New line",
        widget=forms.Textarea,
    )

    content_type = forms.ChoiceField(choices=Post.TEXT_CONTENT_TYPES)

    upload_content_type = forms.ChoiceField(
        choices=[("", "")] + Post.IMAGE_CONTENT_TYPES,
        required=False,
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

        self.save_visible_to(instance, commit)

        delete_child = False

        upload_content_type = self.cleaned_data["upload_content_type"]
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
                    categories=instance.categories.all(),
                )

            instance.child_post.content_type = upload_content_type
            instance.child_post.content = base64.b64encode(file_content.read())
        elif instance.child_post is not None and not upload_content_type:
            delete_child = True

        if commit:
            instance.save()
            self.save_m2m()

            if instance.child_post:
                if delete_child:
                    instance.child_post.delete()
                else:
                    instance.child_post.save()

        return instance

    def save_categories(self, instance, commit=True):
        instance.categories.clear()

        categories_string = self.cleaned_data["categories"]
        if categories_string:
            for name in categories_string.split(" "):
                if not instance.categories.filter(name=name).exists():
                    category = Category.objects.filter(name=name).first()

                    if category is None:
                        category = Category.objects.create(name=name)

                    instance.categories.add(category)

    def save_visible_to(self, instance, commit=True):
        authors_uris_string = self.cleaned_data["visible_to"]

        if authors_uris_string:
            for author_uri_string in authors_uris_string.split('\n'):
                author_uuid = Author.get_id_from_uri(author_uri_string)
                author_uuid = uuid.UUID(author_uuid)

                if not instance.visible_to.filter(id=author_uuid).exists():
                    author, created = Author.objects.get_or_create(id=author_uuid)
                    self.cleaned_data["visible_to"] = author_uuid

                    instance.visible_to.add(author)

    # Source:
    # https://docs.djangoproject.com/en/1.10/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
    def clean(self):
        cleaned_data = super(PostForm, self).clean()
        upload_content = cleaned_data["upload_content"]
        upload_content_type = cleaned_data["upload_content_type"]

        is_insert = not Post.objects.filter(id=self.instance.id).exists()

        # upload_content and type must either both be set or both not be set
        if is_insert:
            if (upload_content and not upload_content_type) or (not upload_content and upload_content_type):
                raise forms.ValidationError(
                    "Upload content type can only be set if an image is uploaded, and vice-versa.")
        else:
            if upload_content:
                if not upload_content_type:
                    raise forms.ValidationError("Uploading a new image requires an upload content type.")
            elif (self.instance.child_post
                  and upload_content_type  # Not setting the upload content type deletes an existing image
                  and upload_content_type != self.instance.child_post.content_type):
                raise forms.ValidationError("Can't change the content type of an existing image.")

    class Meta:
        model = Post
        fields = ["title", "description", "content_type", "content", "visibility", "unlisted"]
