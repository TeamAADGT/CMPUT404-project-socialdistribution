import feedparser
import re

from background_task import background

from social.app.models.author import Author
from social.app.models.post import Post

# Get the GitHub activity of a user
# Reference source: https://pypi.python.org/pypi/django-background-tasks
@background(schedule=60)
def get_github_activity(author_id):
    git_author = Author.objects.get(id=author_id)
    git_url = git_author.github

    # Using RegEx to check if it's a proper URL
    # Reference source: https://github.com/lorey/social-media-profiles-regexs#github
    # TODO: Fix this so that it won't continue if given something like /user/repo
    # (although it won't cause an error if it receives a wrong input it's just something that bugs me)
    if(re.match(r'http(s)?:\/\/(www\.)?github\.com/[A-z 0-9 _ -]+\/?', git_url) is not None):
        if(git_url[-1:] == "/"):
            git_url = git_url[:-1]
        data = feedparser.parse(git_url + ".atom")

        # Get encoding to decode the data
        encoding = data["encoding"]

        # Go over all the entries for the RSS feed, turn them into posts (if possible), save them
        for x in data.get("entries"):
            git_id = x["id"].encode(encoding)
            git_title = x["title"].encode(encoding)
            content_str = "See [this page](%s)" %(x["link"].encode(encoding))

            # Create or update the post
            # Reference source: https://docs.djangoproject.com/en/1.10/ref/models/querysets/#update-or-create
            post, created = Post.objects.update_or_create(github_id=git_id,
                             defaults={"author": git_author,
                                       "title": "New GitHub Activity",
                                       "github_id": git_id,
                                       "description": git_title,
                                       "content_type": "text/markdown",
                                       "content": content_str,
                                       "published": x["published"].encode(encoding)},
                           )