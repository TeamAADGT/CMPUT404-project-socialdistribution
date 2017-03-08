from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
import uuid

# Create your models here.

#
# The user model is described by this specification:
# https://github.com/TeamAADGT/CMPUT404-project-socialdistribution/blob/master/example-article.json
#

# Code based on ideas by
# Nkansah Rexford (https://plus.google.com/+NkansahRexford?prsrc=5) from
# https://blog.khophi.co/extending-django-user-model-userprofile-like-a-pro/


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='user')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    displayName = models.CharField(max_length=512)

    ### Optional Attributes

    # https://github.com/join
    githubUsername = models.CharField(default='', blank=True, max_length=39)

    bio = models.TextField(default='', blank=True)

    ### Meta Attributes

    # Some meta-data for server-server communications
    host = models.TextField(editable=False)
    url = models.URLField(editable=False)


def create_profile(sender, **kwargs):
    user = kwargs["instance"]
    if kwargs["created"]:
        user_profile = UserProfile(user=user)
        user_profile.displayName = user_profile.user.first_name + ' ' + user_profile.user.last_name
        user_profile.save()

post_save.connect(create_profile, sender=User)

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])
