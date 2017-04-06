import feedparser
from background_task import background
from social.app.models.author import Author
from social.app.models.post import Post

# Get the GitHub activity of a user
# Source: https://pypi.python.org/pypi/django-background-tasks
@background(schedule=60)
def get_github_activity(authorId, gitUrl):
    print("Entered!")
    gitAuthor = Author.objects.get(id=authorId)

    # lazy way of checking if URL is correct right now
    if((gitUrl[:19] == "https://github.com/") and (len(gitUrl.split("/")) == 4)):
        data = feedparser.parse(gitUrl + ".atom")

        # get users post
        posts = Post.objects.filter(author__id=authorId).filter(title__contains="New GitHub Activity:")

        # Get encoding to decode the data
        encoding = data["encoding"]
        # Go over all the entries for the RSS feed, turn them into posts, save
        # them - this seems to work out okay imo
        for x in data.get("entries"):
            found = False
            gitId = x["id"].encode(encoding).split("/")

            # This is done to avoid adding duplicates
            for post in posts:
                entry = post.title.split()
                if(entry[3] == gitId[1]):
                    found = True
                    break
        
            if(found is False):
                post = Post.objects.create(author=gitAuthor)

                # want to stash activity ID somewhere to avoid duplication in later gets
                # it's in the title right now, just need to actually get it
                post.title = "New GitHub Activity: %s" %gitId[1]
                # uses given title to describe what the user did
                post.description = x["title"].encode(encoding)
                post.content_type = "text/markdown"
                # gives a link to the page
                post.content = "See [this page](%s)" %(x["link"].encode(encoding))
                # use their given published date so that way it's properly sorted
                post.published = x["published"].encode(encoding)
                post.save()