import base64

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from social.app.models.author import Author
from social.app.models.node import Node


class AuthorProfileTestCase(APITestCase):
    def setUp(self):
        node = Node.objects.create(name="Test", host="http://www.local.com/",
                                   service_url="http://www.local.com/service/", local=True)

        self.authorized_node = Node.objects.create(name='Remote Node', host='http://www.remote.com/',
                                                   service_url='http://www.remote.com/service/', local=False,
                                                   incoming_username='remote', incoming_password='password', )

        adam_user = User.objects.create_user("adam", "adam@test.com", "pass1")
        bob_user = User.objects.create_user("bob", "bob@test.com", "pass2")

        # Local Users
        self.adam = adam_user.profile
        self.adam.node = node
        self.adam.save()

        self.bob = bob_user.profile
        self.bob.node = node
        self.bob.save()

        self.headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(
                '{}:{}'.format(self.authorized_node.incoming_username,
                               self.authorized_node.incoming_password)),
        }

    def test_get_author_profile(self):
        response = self.client.get(reverse('service:author-detail', args=[self.adam.id]), **self.headers)

        # Assert the response status
        self.assertTrue(response.status_code, 200)

        # Assert the response type
        self.assertEqual(response.accepted_media_type, u'application/json',
                         msg='Expected the response to be "application/json"')

        data = response.data

        self.assertTrue(
            all(keys in data for keys in Author.required_fields),
            msg='Expected keys {} to exist in the response'.format(", ".join(Author.required_fields)))
