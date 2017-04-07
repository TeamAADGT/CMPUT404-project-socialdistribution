import feedparser
import re

from background_task import background

from social.app.models.author import Author
from social.app.models.post import Post

# Get the GitHub activity of a user
# Reference source: https://pypi.python.org/pypi/django-background-tasks
@background(schedule=60)
def get_github_activity(authorId):
    gitAuthor = Author.objects.get(id=authorId)
    gitUrl = gitAuthor.github
    print("Entered")

    # Using RegEx to check if it's a proper URL
    # Reference source: 
    if((gitUrl[:19] == "https://github.com/")):
        data = feedparser.parse(gitUrl + ".atom")

        # get users post
        posts = Post.objects.filter(author__id=authorId).filter(title__contains="New GitHub Activity:")

        # Get encoding to decode the data
        encoding = data["encoding"]

        # Go over all the entries for the RSS feed, turn them into posts (if possible), save them
        for x in data.get("entries"):
            found = False
            gitId = x["id"].encode(encoding)
            gitTitle = x["title"].encode(encoding)
            publishDate = x["published"].encode(encoding)
            contentStr = "See [this page](%s)" %(x["link"].encode(encoding))

            # Create or update the post
            # Reference source: https://docs.djangoproject.com/en/1.10/ref/models/querysets/#update-or-create
            post, created = Post.objects.update_or_create(github_id=gitId,
                             defaults={"author": gitAuthor,
                                       "title": "New GitHub Activity",
                                       "github_id": gitId,
                                       "description": gitTitle,
                                       "content_type": "text/markdown",
                                       "content": contentStr,
                                       "published": publishDate},
                           )

        '''
            for post in posts:
               
                #entry = post.title.split()
                #if(entry[3] == gitId[1]):
                #    found = True
                #    break

            if(found is False):
                post = Post.objects.create(author=gitAuthor)

                post.title = "New GitHub Activity"
                post.githubId = gitId[1]
                # uses given title to describe what the user did
                post.description = x["title"].encode(encoding)
                post.content_type = "text/markdown"
                # gives a link to the page
                post.content = "See [this page](%s)" %(x["link"].encode(encoding))
                # use their given published date so that way it's properly sorted
                post.published = x["published"].encode(encoding)
                post.save()
        '''