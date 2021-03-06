from __future__ import unicode_literals
import re


class FriendRequest(object):
    def __init__(self, query, author, friend):
        self.query = query
        self.author = author
        self.friend = friend


class FriendRequestAuthor(object):
    def __init__(self, id, host, displayName, url):
        self.id = id
        self.host = host
        self.displayName = displayName
        self.url = url
