import base64
import urlparse
import uuid

from datetime import datetime, time, date

import pytz
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from social.app.models.author import Author
from social.app.models.comment import Comment
from social.app.models.node import Node
from social.app.models.post import Post


class PostsTestCase(APITestCase):
    def setUp(self):
        node = Node.objects.create(name="Test", host="http://www.local.com/",
                                   service_url="http://www.local.com/service/", local=True,
                                   incoming_username='local', incoming_password='password', )

        self.authorized_node = Node.objects.create(name='Remote Node', host='http://www.remote.com/',
                                                   service_url='http://www.remote.com/service/', local=False,
                                                   incoming_username='remote', incoming_password='password', )

        adam_user = User.objects.create_user("adam", "adam@test.com", "pass1")
        bob_user = User.objects.create_user("bob", "bob@test.com", "pass2")
        chris_user = User.objects.create_user("chris", "chris@test.com", "pass3")

        # Local Users
        self.adam = adam_user.profile
        self.adam.node = node
        self.adam.save()

        self.bob = bob_user.profile
        self.bob.node = node
        self.bob.save()

        # Remote Users
        self.chris = chris_user.profile
        self.chris.node = self.authorized_node
        self.chris.save()

        dates = [  # Creates several dates from oldest to newest
            datetime.combine(
                date(year=2000 + x, month=(x % 12) + 1, day=(x % 28) + 1),
                time(hour=(x % 23) + 1, minute=(x % 59) + 1, tzinfo=pytz.timezone('America/Edmonton')))
            for x in range(0, 35)
        ]

        self.adam_post_with_comment = Post.objects.create(
            author=self.adam,
            title="Hello I am Adam! Please comment on me!",
            description="Description of Adam",
            content_type="text/plain",
            content="Content of Adam",
            visibility="PUBLIC",
            published=dates[21],
        )

        self.adam_comments_on_post = [
            Comment.objects.create(
                comment="Welcome, Adam! I'm the first poster!",
                author=self.bob,
                post=self.adam_post_with_comment,
                published=dates[22],
            ),

            Comment.objects.create(
                comment="Third post!",
                author=self.bob,
                post=self.adam_post_with_comment,
                published=dates[29],
            ),

            Comment.objects.create(
                comment="Second post!",
                author=self.bob,
                post=self.adam_post_with_comment,
                published=dates[25],
            ),

            Comment.objects.create(
                comment="Fourth (REMOTE) post!",
                author=self.chris,
                post=self.adam_post_with_comment,
                published=dates[30],
            ),
        ]

        self.adam_post_without_a_comment = Post.objects.create(
            author=self.adam,
            title="Hello I am Adam",
            description="Description of Adam",
            content_type="text/plain",
            content="Content of Adam",
            visibility="PUBLIC",
            published=dates[10],
        )

        all_posts = [

            ### Adam's Posts
            # Note that the published dates are inter-leaved with Bob's posts in order to test the sort order

            self.adam_post_without_a_comment,

            Post.objects.create(
                author=self.adam,
                title="My Second Post",
                description="Coolbears description of my second post",
                content_type="text/markdown",
                content="Second post contents using [Markdown](http://example.com/).",
                visibility="PUBLIC",
                published=dates[15],
            ),

            self.adam_post_with_comment,

            # Non-public posts
            Post.objects.create(
                author=self.adam,
                title="My Third SECRET/PRIVATE Post",
                description="Top secrete description of my third post",
                content_type="text/plain",
                content="Third post contents. The content is very secret!",
                visibility="PRIVATE",
                published=dates[20],
            ),

            ### Bob's Posts
            # Note that the published dates are inter-leaved with Adam's posts in order to test the sort order

            Post.objects.create(
                author=self.bob,
                title="Hello I am Bob",
                description="Description of Bob",
                content_type="text/plain",
                content="Content of Bob",
                visibility="PUBLIC",
                published=dates[0],
            ),
            Post.objects.create(
                author=self.bob,
                title="My Second Post",
                description="Coolbears description of my second post",
                content_type="text/markdown",
                content="Second post contents using [Markdown](http://example.com/).",
                visibility="PUBLIC",
                published=dates[18],
            ),

            # Non-public posts
            Post.objects.create(
                author=self.bob,
                title="My Third SECRET/PRIVATE Post",
                description="Top secret description of my third post",
                content_type="text/plain",
                content="Third post contents. The content is very secret!",
                visibility="PRIVATE",
                published=dates[2],
            ),

            ### Remote Node Posts
            Post.objects.create(
                author=self.chris,
                title="A secrete remote node post",
                description="Top secret description of my remote post",
                content_type="text/markdown",
                content="Very very secret!",
                visibility="PRIVATE",
                published=dates[12],
            ),

            Post.objects.create(
                author=self.chris,
                title="Remote Public Post",
                description="Add 1/2 tablespoons of sugar.",
                content_type="text/plain",
                content="Bake for 30 minutes.",
                visibility="PUBLIC",
                published=dates[7],
            ),
        ]

        self.all_local_posts = filter(lambda p: p.author.node.local == True, all_posts)

        self.all_local_posts_sorted = sorted(self.all_local_posts, key=lambda p: p.published, reverse=True)

        self.local_public_posts = filter(lambda p: p.visibility == 'PUBLIC', self.all_local_posts)
        self.local_public_posts_sorted = sorted(self.local_public_posts, key=lambda p: p.published, reverse=True)
        self.local_private_posts = filter(lambda p: p.visibility == 'PRIVATE', self.all_local_posts)
        self.local_adam_posts = filter(lambda p: p.author == self.adam, self.all_local_posts)
        self.local_adam_posts_sorted = sorted(self.local_adam_posts, key=lambda p: p.published, reverse=True)
        self.adam_comments_on_post_sorted = sorted(self.adam_comments_on_post, key=lambda p: p.published, reverse=True)
        self.bob_posts = filter(lambda p: p.author == self.bob, all_posts)

        # All URLs for the post API calls
        self.urls = {
            "posts": reverse("service:public-posts-list"),
            "author/posts": reverse("service:all-posts-list"),
            "author/adam/posts": reverse("service:author-posts-list", args=[self.adam.id]),
            "posts/adam_post_with_comment/comments": reverse("service:post-comments-list",
                                                             args=[self.adam_post_with_comment.id]),
            "posts/post_without_a_comment/comments": reverse("service:post-comments-list",
                                                             args=[self.adam_post_without_a_comment.id]),
            "author/bob/posts": reverse("service:author-posts-list", args=[self.bob.id]),
        }

        for index, post in enumerate(self.all_local_posts):
            self.urls["posts/<%d>" % index] = reverse("service:post-detail", args=[post.id])

        self.headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(
                '{}:{}'.format(self.authorized_node.incoming_username,
                               self.authorized_node.incoming_password)),
        }

    def test_service_posts_have_correct_response_as_authorized_user(self):
        for key, url in self.urls.items():
            response = self.client.get(url, **self.headers)

            # Assert the response status
            self.assertTrue(response.status_code, 200)

            # Assert the response type
            self.assertEqual(response.accepted_media_type, u'application/json',
                             msg='Expected the response to be "application/json"')

            data = response.data

            # Assert the required keys
            required_post_keys = Post.required_header_fields
            required_post_comments_keys = Comment.required_header_fields
            required_keys = set()
            query_value = ''

            if url.endswith('/comments'):
                required_keys = required_post_comments_keys
                query_value = 'comments'
            else:
                required_keys = required_post_keys
                query_value = 'posts'

            self.assertTrue(
                all(keys in data for keys in required_keys),
                msg='Expected keys {} to exist in the response {}'.format(", ".join(required_keys), data))

            # Assert the key values where possible
            self.assertEqual(data['query'], query_value)

    def test_service_posts_have_correct_response_as_anonymous_user(self):
        for key, url in self.urls.items():
            response = self.client.get(url)

            # Only the /posts endpoint should be accessible publically
            if key == 'posts':
                # Assert the response status
                self.assertTrue(response.status_code, 200)

                # Assert the response type
                self.assertEqual(response.accepted_media_type, u'application/json',
                                 msg='Expected the response to be "application/json"')

                data = response.data

                # Assert the required keys
                required_keys = Post.required_header_fields
                self.assertTrue(all(keys in data for keys in required_keys),
                                msg='Expected keys {} to exist in the response'.format(", ".join(required_keys)))

                # Assert the key values where possible
                self.assertEqual(data['query'], 'posts')
            else:
                # Assert the response status
                self.assertTrue(response.status_code, 401)

    def test_get_service_posts_public_has_required_keys_and_values(self):
        response = self.client.get(self.urls['posts'])

        for post_json in response.data['posts']:
            # Assert the required keys
            required_keys = Post.required_fields
            self.assertTrue(
                all(keys in post_json for keys in required_keys),
                msg='Expected keys {} to exist in the response'.format(", ".join(required_keys)))

            required_author_keys = Author.required_fields
            self.assertTrue(
                all(keys in post_json['author'] for keys in required_author_keys),
                msg='Expected keys {} to exist in the post#author response'.format(", ".join(required_keys)))

            for comment_json in post_json['comments']:
                required_comment_keys = Comment.required_fields
                self.assertTrue(
                    all(keys in comment_json for keys in required_comment_keys),
                    msg='Expected keys {} to exist in the post#comment response'.format(", ".join(required_keys)))

                self.assertTrue(
                    all(keys in comment_json['author'] for keys in required_author_keys),
                    msg='Expected keys {} to exist in the post#comment#author response'.format(
                        ", ".join(required_keys)))

    def test_get_service_posts_public_has_filtered_out_private_posts_as_anonymous_user(self):
        response = self.client.get(self.urls['posts'])

        data = response.data
        posts = data['posts']

        self.assertEquals(len(posts), len(self.local_public_posts),
                          msg="The service responded with {} posts but we expected {} posts.".format(
                              len(posts), len(self.local_public_posts)))

    def test_get_service_posts_public_has_filtered_out_private_posts_as_authenticated_user(self):
        response = self.client.get(self.urls['posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEquals(len(posts), len(self.local_public_posts),
                          msg="The service responded with {} posts but we expected {} posts.".format(
                              len(posts), len(self.local_public_posts)))

    def test_get_service_author_posts_has_all_posts(self):  # Tests /author/posts
        response = self.client.get(self.urls['author/posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEquals(len(posts), len(self.all_local_posts),
                          msg="The service responded with {} posts but we expected {} posts.".format(
                              len(posts), len(self.all_local_posts)))

    def test_get_service_author_adam_posts_has_only_adam_posts(self):  # Tests /author/<adam_id>/posts
        response = self.client.get(self.urls['author/adam/posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEquals(len(posts), len(self.local_adam_posts),
                          msg="The service responded with {} posts but we expected {} posts.".format(
                              len(posts), len(self.local_adam_posts)))

    def test_get_service_author_bob_posts_has_only_bob_posts(self):  # Tests /author/<bob_id>/posts
        response = self.client.get(self.urls['author/bob/posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEquals(len(posts), len(self.bob_posts),
                          msg="The service responded with {} posts but we expected {} posts.".format(
                              len(posts), len(self.bob_posts)))

    def test_get_service_author_adam_post_comments(self):  # Tests /posts/<adam_post_with_comments_id>/comments
        response = self.client.get(self.urls['posts/adam_post_with_comment/comments'], **self.headers)

        data = response.data
        posts = data['comments']

        number_of_post_comments = Comment.objects.filter(post=self.adam_post_with_comment).count()

        self.assertEquals(len(posts), number_of_post_comments,
                          msg="The service responded with {} posts but we expected {} posts.".format(
                              len(posts), number_of_post_comments))

    def test_get_service_author_adam_post_with_no_comments(self):  # Tests /posts/<post_without_a_comment_id>/comments
        response = self.client.get(self.urls['posts/post_without_a_comment/comments'], **self.headers)

        data = response.data
        posts = data['comments']

        number_of_post_comments = Comment.objects.filter(post=self.adam_post_without_a_comment).count()
        self.assertEquals(number_of_post_comments, 0)  # Will only fail if someone changed adam_post_without_a_comment

        self.assertEquals(len(posts), 0, msg="The service responded with {} posts but we expected {} posts.".format(
            len(posts), 0))

    # Validate the returned sort order is from newest to oldest
    def test_get_service_posts_public_sort_order(self):
        response = self.client.get(self.urls['posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEqual(len(posts), len(self.local_public_posts_sorted))

        for index, post in enumerate(posts):
            self.assertEqual(uuid.UUID(post['id']), self.local_public_posts_sorted[index].id)

    # Validate the returned sort order is from newest to oldest
    def test_get_service_author_posts_sort_order(self):
        response = self.client.get(self.urls['author/posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEqual(len(posts), len(self.all_local_posts_sorted))

        for index, post in enumerate(posts):
            self.assertEqual(uuid.UUID(post['id']), self.all_local_posts_sorted[index].id)

    # Validate the returned sort order is from newest to oldest
    def test_get_service_author_adam_posts_sort_order(self):
        response = self.client.get(self.urls['author/adam/posts'], **self.headers)

        data = response.data
        posts = data['posts']

        self.assertEqual(len(posts), len(self.local_adam_posts_sorted))

        for index, post in enumerate(posts):
            self.assertEqual(uuid.UUID(post['id']), self.local_adam_posts_sorted[index].id)

    # Validate the returned sort order is from newest to oldest
    def test_get_service_author_adam_post_comments_sort_order(self):
        response = self.client.get(self.urls['posts/adam_post_with_comment/comments'], **self.headers)

        data = response.data
        comments = data['comments']

        self.assertEqual(len(comments), len(self.adam_comments_on_post_sorted))

        for index, post in enumerate(comments):
            self.assertEqual(uuid.UUID(post['id']), self.adam_comments_on_post_sorted[index].id)

    def mock_comment_post_data(self, post):
        return {
            'query': 'addComment',
            'post': urlparse.urljoin(self.authorized_node.host, 'posts/' + str(post.id)),
            'comment': {
                'author': {
                    'id': urlparse.urljoin(self.authorized_node.host, 'author/' + str(self.chris.id)),
                    'host': self.authorized_node.service_url,
                    'displayName': self.chris.displayName,
                    'url': urlparse.urljoin(self.authorized_node.host, 'author/' + str(self.chris.id)),
                },
                'comment': "[New Comment]('http://www.remote.com/)",
                'contentType': 'text/markdown',
                'published': '2015-03-09T13:07:04+00:00',
                'id': uuid.uuid4(),
            }
        }

    '''
    def test_post_service_posts_add_remote_comment_to_public_post(self):
        post = self.local_public_posts[0]
        data = self.mock_comment_post_data(post)
        response = self.client.post(reverse("service:post-comments-list", args=[post.id]),
                                    data=data, format='json', **self.headers)
        self.assertEquals(response.status_code, 200)

        required_keys = ('query', 'success', 'message')
        self.assertTrue(
            all(keys in data for keys in required_keys),
            msg='Expected keys {} to exist in the response'.format(", ".join(required_keys)))

        self.assertEquals(data['query'], 'addComments')
        self.assertEquals(data['success'], True)
        self.assertEquals(data['message'], 'Comment not allowed')

    def test_post_service_posts_add_remote_comment_to_private_post(self):
        post = self.local_private_posts[0]
        data = self.mock_comment_post_data(post)
        response = self.client.post(reverse("service:post-comments-list", args=[post.id]), data=data, format='json',
                                    **self.headers)
        self.assertEquals(response.status_code, 403)

        # Assert the data response
        data = response.data

        self.assertEqual(response.accepted_media_type, u'application/json',
                         msg='Expected the response to be "application/json"')

        required_keys = ('query', 'success', 'message')
        self.assertTrue(
            all(keys in data for keys in required_keys),
            msg='Expected keys {} to exist in the response'.format(", ".join(required_keys)))

        self.assertEquals(data['query'], 'addComments')
        self.assertEquals(data['success'], False)
        self.assertEquals(data['message'], 'Comment not allowed')
    '''
