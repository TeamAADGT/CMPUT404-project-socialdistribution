import base64, uuid, logging

from django import forms
from rest_framework.reverse import reverse

from social.app.models.category import Category
from social.app.models.post import Post
from social.app.models.author import Author
from social.app.models.authorlink import AuthorLink
from service import urls


class PostForm(forms.ModelForm):

    visible_to_author = forms.CharField(
        label="Visible to authors",
        required=False,
        help_text="Single author link per line",
        widget=forms.Textarea,
    )

    categories = forms.CharField(
        label="Categories",
        required=False,
        help_text="Space-delimited",
    )

    content_type = forms.ChoiceField(choices=Post.TEXT_CONTENT_TYPES)

    upload_content_type = forms.ChoiceField(
        choices=[("", "")] + Post.IMAGE_CONTENT_TYPES,
        required=False,
    )

    upload_content = forms.FileField(
        required=False
    )

    field_order = ["title", "description", "content_type", "content", "categories", "unlisted",
                   "visibility", "visible_to_author", "upload_content_type", "upload_content" ]

    def save(self, *args, **kwargs):
        # NOTE: due to complexities with categories, and visible_to_author, commit=False is not respected!
        request = kwargs["request"]

        instance = super(PostForm, self).save(commit=False)

        instance.author = request.user.profile
        instance.source = reverse('service:post-detail', kwargs = {'pk':instance.id}, request=request)
        instance.origin = instance.source

        instance.save()
        self.save_categories(instance)

        self.save_visible_to_author(instance)

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
                    visible_to_author=instance.visible_to_author.all(),
                    categories=instance.categories.all(),
                )

            instance.child_post.content_type = upload_content_type
            instance.child_post.content = base64.b64encode(file_content.read())
        elif instance.child_post is not None and not upload_content_type:
            delete_child = True

        instance.save()

        if instance.child_post:
            if delete_child:
                instance.child_post.delete()
            else:
                instance.child_post.save()

        return instance

    def save_categories(self, instance):
        categories_string = self.cleaned_data["categories"]
        category_names = categories_string.split(' ') if categories_string else []
        categories = [Category.objects.get_or_create(name=name)[0] for name in category_names]
        instance.categories.set(categories)

    def save_visible_to_author(self, instance):
        instance.visible_to_author.clear()

        authors_uris_string = self.cleaned_data["visible_to_author"]
        if authors_uris_string:
            for author_uri_string in authors_uris_string.splitlines():
                author_uri_string = author_uri_string.strip()
                try:
                    Author.get_id_from_uri(author_uri_string)
                    if not instance.visible_to_author.filter(uri=author_uri_string).exists():
                        author_uri, created = AuthorLink.objects.get_or_create(uri=author_uri_string)

                        instance.visible_to_author.add(author_uri)
                except Exception as e:
                    logging.error(e)
                    logging.error("Invalid Author Link")


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
