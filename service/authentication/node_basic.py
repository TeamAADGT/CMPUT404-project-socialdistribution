import os

from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed

from social.app.models.node import Node


class NodeBasicAuthentication(BasicAuthentication):
    """
    Source: http://www.django-rest-framework.org/api-guide/authentication/#custom-authentication
    and https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authentication.py
    
    Set up the keys in Heroku via this process: 
    https://devcenter.heroku.com/articles/config-vars#setting-up-config-vars-for-a-deployed-application
    """

    USERNAME_KEY = "SOCDIS_USERNAME"
    PASSWORD_KEY = "SOCDIS_PASSWORD"

    def __init__(self):
        self.node = None

    def authenticate(self, request):
        host = request.META["REMOTE_HOST"] or request.META["REMOTE_ADDR"]

        if host == "127.0.0.1" and request.META["SERVER_PORT"] != "80":
            # For local testing purposes
            host = "%s:%s" % (host, request.META["SERVER_PORT"])

        try:
            self.node = Node.objects.get(host=host)
        except Node.DoesNotExist:
            # Request doesn't match a known node -- failed
            raise AuthenticationFailed("Request comes from unknown remote server.")

        if self.node.local or not self.node.requires_auth:
            return self.node, None

        return super(NodeBasicAuthentication, self).authenticate(request)

    def authenticate_credentials(self, userid, password):
        if self.USERNAME_KEY in os.environ and self.PASSWORD_KEY in os.environ:
            expected_username = os.environ[self.USERNAME_KEY]
            expected_password = os.environ[self.PASSWORD_KEY]

            if expected_username and expected_password \
                    and userid == expected_username and password == expected_password:
                return self.node, None

        raise AuthenticationFailed("Invalid username/password.")
