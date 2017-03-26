from rest_framework.authentication import BaseAuthentication, BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed

from social.app.models.node import Node


class NodeBasicAuthentication(BasicAuthentication):
    """
    Source: http://www.django-rest-framework.org/api-guide/authentication/#custom-authentication
    and https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authentication.py
    """

    def __init__(self):
        self.node = None

    def authenticate(self, request):
        host = request.META["REMOTE_HOST"]
        try:
            self.node = Node.objects.get(host=host)
        except Node.DoesNotExist:
            # Request doesn't match a known node -- failed
            raise AuthenticationFailed("Request comes from unknown remote server.")

        if not self.node.requires_auth:
            return self.node, None

        return super(NodeBasicAuthentication, self).authenticate(request)

    def authenticate_credentials(self, userid, password):
        if userid == self.node.username and password == self.node.password:
            return self.node, None

        raise AuthenticationFailed("Invalid username/password.")
