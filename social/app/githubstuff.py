# Note that this isn't a proper Python/Django file and it'll need to be integrated
# into the actual Django stuff
import feedparser

...

def getGitHubPages():
    # get RSS feed data using feedparser
    # my RSS feed used as a default
    data = feedparser.parse("https://github.com/tiegan.atom")

    # Get encoding to decode the data
    encoding = data["encoding"]
    # Go over all the entries for the RSS feed, turn them into posts, save
    # them - this seems to work out okay imo
    for x in data.get("entries"):
        post = Post.objects.create() #author_id="b5357e6874424df1af124fbb40d6621f"

        # want to stash activity ID somewhere to avoid duplication in later gets
        # it's in the title right now, just need to actually get it
        post.title = "New GitHub Activity: %s" %x["id"].encode(encoding)
        # uses given title to describe what the user did
        post.description = x["title"].encode(encoding)
        post.content_type = "text/markdown"
        # gives a link to the page
        post.content = "See [this page](%s)" %(x["link"].encode(encoding))
        # use their given published date so that way it's properly sorted
        post.published = x["published"].encode(encoding)
        post.save()

# Need to figure out how exactly to call this within our website itself
# That's really the main issue persisting right now

# Also need to make sure the given GitHub URL is proper (i.e. https://github.com/(user))