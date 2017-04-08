import uuid

from django.db import models

from social.app.models.author import Author
from social.app.models.post import Post


# Based on code by Django Girls, url:
# https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/homework_create_more_models/
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        verbose_name="author of the comment",
    )

    comment = models.TextField()
    published = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('published',)

    def __str__(self):
        return 'Comment by {} on {}: {}'.format(self.author, self.post, self.text)
